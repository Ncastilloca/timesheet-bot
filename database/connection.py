import sqlite3, logging, os
from contextlib import contextmanager

logger = logging.getLogger(__name__)
DB = os.getenv("DATABASE_URL", "timesheet.db")

def get_conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

@contextmanager
def tx():
    c = get_conn()
    try:
        yield c
        c.commit()
    except Exception as e:
        c.rollback()
        logger.error(f"DB error: {e}")
        raise
    finally:
        c.close()

def init_db():
    with tx() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS employee (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL UNIQUE,
            name        TEXT    NOT NULL,
            hourly_rate REAL,
            tax_percent REAL,
            language    TEXT NOT NULL DEFAULT 'es',
            time_format TEXT NOT NULL DEFAULT '12h',
            date_format TEXT NOT NULL DEFAULT 'MM/DD/YYYY',
            timezone    TEXT NOT NULL DEFAULT 'America/New_York',
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS payroll_period (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date  TEXT NOT NULL,
            end_date    TEXT,
            is_active   INTEGER NOT NULL DEFAULT 1,
            total_hours REAL    NOT NULL DEFAULT 0.0,
            notes       TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            closed_at   TEXT
        );
        CREATE TABLE IF NOT EXISTS time_entry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id   INTEGER NOT NULL REFERENCES payroll_period(id) ON DELETE CASCADE,
            work_date   TEXT NOT NULL,
            time_in     TEXT NOT NULL,
            time_out    TEXT NOT NULL,
            total_hours REAL NOT NULL DEFAULT 0.0,
            notes       TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(period_id, work_date)
        );
        CREATE INDEX IF NOT EXISTS idx_ep ON time_entry(period_id);
        CREATE INDEX IF NOT EXISTS idx_pa ON payroll_period(is_active);
        """)
        # Migrate older DBs
        cols = {r[1] for r in c.execute("PRAGMA table_info(employee)")}
        for col, defn in [
            ("hourly_rate","REAL"), ("tax_percent","REAL"),
            ("language","TEXT NOT NULL DEFAULT 'es'"),
            ("time_format","TEXT NOT NULL DEFAULT '12h'"),
            ("date_format","TEXT NOT NULL DEFAULT 'MM/DD/YYYY'"),
            ("timezone","TEXT NOT NULL DEFAULT 'America/New_York'"),
        ]:
            if col not in cols:
                c.execute(f"ALTER TABLE employee ADD COLUMN {col} {defn}")
        pcols = {r[1] for r in c.execute("PRAGMA table_info(payroll_period)")}
        if "notes" not in pcols:
            c.execute("ALTER TABLE payroll_period ADD COLUMN notes TEXT")
    logger.info("Database ready.")
