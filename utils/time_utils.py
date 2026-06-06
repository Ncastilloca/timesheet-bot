from datetime import datetime, date, timedelta
from typing import Optional

TIME_FMTS = ["%I:%M %p","%I:%M%p","%H:%M","%I %p","%I%p"]
DATE_FMTS  = ["%m/%d/%Y","%Y-%m-%d","%m-%d-%Y","%m/%d/%y","%d/%m/%Y","%B %d, %Y"]

def parse_time(raw: str) -> Optional[datetime]:
    for f in TIME_FMTS:
        try: return datetime.strptime(raw.strip().upper(), f)
        except: pass
    return None

def parse_date(raw: str) -> Optional[date]:
    for f in DATE_FMTS:
        try: return datetime.strptime(raw.strip(), f).date()
        except: pass
    return None

def calc_hours(tin: str, tout: str) -> Optional[float]:
    t1 = datetime.strptime(tin,  "%H:%M")
    t2 = datetime.strptime(tout, "%H:%M")
    if t2 <= t1: return None
    return round((t2-t1).total_seconds()/3600, 2)

def fmt_hours(h: float) -> str:
    hh = int(h); mm = round((h-hh)*60)
    return f"{hh}h" if mm==0 else f"{hh}h {mm}m"

def fmt_time(ts: str, fmt="12h") -> str:
    try:
        dt = datetime.strptime(ts, "%H:%M")
        return dt.strftime("%I:%M %p") if fmt=="12h" else dt.strftime("%H:%M")
    except: return ts

def fmt_date(ds: str, fmt="MM/DD/YYYY") -> str:
    try:
        d = datetime.strptime(ds, "%Y-%m-%d")
        if fmt=="DD/MM/YYYY": return d.strftime("%d/%m/%Y")
        if fmt=="YYYY-MM-DD": return ds
        return d.strftime("%m/%d/%Y")
    except: return ds

def today() -> str: return date.today().isoformat()
def store_date(d: date) -> str: return d.isoformat()
def store_time(dt: datetime) -> str: return dt.strftime("%H:%M")

def day_abbr(ds: str, lang="es") -> str:
    try:
        day = datetime.strptime(ds, "%Y-%m-%d").strftime("%a")
        if lang=="es":
            return {"Mon":"Lun","Tue":"Mar","Wed":"Mié","Thu":"Jue","Fri":"Vie","Sat":"Sáb","Sun":"Dom"}.get(day,day)
        return day
    except: return ""
