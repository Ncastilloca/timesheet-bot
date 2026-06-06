from typing import Optional
from database.connection import tx

# ── Employee ──────────────────────────────────────────────────────

def get_emp(tid: int) -> Optional[dict]:
    with tx() as c:
        r = c.execute("SELECT * FROM employee WHERE telegram_id=?", (tid,)).fetchone()
        return dict(r) if r else None

def upsert_emp(tid: int, name: str) -> dict:
    with tx() as c:
        c.execute("""INSERT INTO employee(telegram_id,name) VALUES(?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET name=excluded.name,updated_at=datetime('now')""",
            (tid, name))
        return dict(c.execute("SELECT * FROM employee WHERE telegram_id=?", (tid,)).fetchone())

def set_emp_field(tid: int, field: str, value) -> dict:
    allowed = {"name","hourly_rate","tax_percent","language","time_format","date_format","timezone"}
    if field not in allowed: raise ValueError(f"Bad field: {field}")
    with tx() as c:
        c.execute(f"UPDATE employee SET {field}=?,updated_at=datetime('now') WHERE telegram_id=?", (value,tid))
        return dict(c.execute("SELECT * FROM employee WHERE telegram_id=?", (tid,)).fetchone())

# ── Payroll Period ────────────────────────────────────────────────

def get_active() -> Optional[dict]:
    with tx() as c:
        r = c.execute("SELECT * FROM payroll_period WHERE is_active=1 ORDER BY id DESC LIMIT 1").fetchone()
        return dict(r) if r else None

def get_period(pid: int) -> Optional[dict]:
    with tx() as c:
        r = c.execute("SELECT * FROM payroll_period WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

def all_periods() -> list:
    with tx() as c:
        return [dict(r) for r in c.execute("SELECT * FROM payroll_period ORDER BY id DESC")]

def create_period(start: str) -> dict:
    with tx() as c:
        c.execute("INSERT INTO payroll_period(start_date) VALUES(?)", (start,))
        return dict(c.execute("SELECT * FROM payroll_period ORDER BY id DESC LIMIT 1").fetchone())

def update_period(pid: int, **kwargs) -> dict:
    allowed = {"start_date","end_date","notes"}
    sets = {k:v for k,v in kwargs.items() if k in allowed}
    if not sets: return get_period(pid)
    sql = ", ".join(f"{k}=?" for k in sets)
    with tx() as c:
        c.execute(f"UPDATE payroll_period SET {sql} WHERE id=?", (*sets.values(), pid))
        return dict(c.execute("SELECT * FROM payroll_period WHERE id=?", (pid,)).fetchone())

def close_period(pid: int, end: str, total: float):
    with tx() as c:
        c.execute("UPDATE payroll_period SET is_active=0,end_date=?,total_hours=?,closed_at=datetime('now') WHERE id=?",
                  (end, total, pid))

def reopen_period(pid: int):
    with tx() as c:
        c.execute("UPDATE payroll_period SET is_active=1,end_date=NULL,closed_at=NULL WHERE id=?", (pid,))

def recalc(pid: int) -> float:
    with tx() as c:
        total = c.execute("SELECT COALESCE(SUM(total_hours),0) FROM time_entry WHERE period_id=?", (pid,)).fetchone()[0]
        c.execute("UPDATE payroll_period SET total_hours=? WHERE id=?", (total,pid))
        return total

# ── Time Entry ────────────────────────────────────────────────────

def get_entries(pid: int) -> list:
    with tx() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM time_entry WHERE period_id=? ORDER BY work_date", (pid,))]

def get_entry(eid: int) -> Optional[dict]:
    with tx() as c:
        r = c.execute("SELECT * FROM time_entry WHERE id=?", (eid,)).fetchone()
        return dict(r) if r else None

def entry_by_date(pid: int, date: str) -> Optional[dict]:
    with tx() as c:
        r = c.execute("SELECT * FROM time_entry WHERE period_id=? AND work_date=?", (pid,date)).fetchone()
        return dict(r) if r else None

def create_entry(pid, date, tin, tout, hours, notes="") -> dict:
    with tx() as c:
        c.execute("INSERT INTO time_entry(period_id,work_date,time_in,time_out,total_hours,notes) VALUES(?,?,?,?,?,?)",
                  (pid,date,tin,tout,hours,notes))
        return dict(c.execute("SELECT * FROM time_entry WHERE period_id=? AND work_date=?", (pid,date)).fetchone())

def update_entry(eid, date, tin, tout, hours, notes="") -> dict:
    with tx() as c:
        c.execute("""UPDATE time_entry SET work_date=?,time_in=?,time_out=?,total_hours=?,
                     notes=?,updated_at=datetime('now') WHERE id=?""",
                  (date,tin,tout,hours,notes,eid))
        return dict(c.execute("SELECT * FROM time_entry WHERE id=?", (eid,)).fetchone())

def delete_entry(eid: int):
    with tx() as c:
        c.execute("DELETE FROM time_entry WHERE id=?", (eid,))
