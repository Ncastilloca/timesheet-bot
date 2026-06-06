from telegram import InlineKeyboardButton as B, InlineKeyboardMarkup as K
from utils.i18n import T

def mk(rows): return K(rows)

def main_menu(e):
    return mk([
        [B(T(e,"b_add"),      callback_data="add_entry"),   B(T(e,"b_period"),     callback_data="current_period")],
        [B(T(e,"b_edit_entry"),callback_data="edit_entry"), B(T(e,"b_del_entry"),  callback_data="del_entry")],
        [B(T(e,"b_history"),  callback_data="history"),     B(T(e,"b_pdf"),        callback_data="export_pdf")],
        [B(T(e,"b_profile"),  callback_data="profile"),     B(T(e,"b_pay"),        callback_data="pay_settings")],
        [B(T(e,"b_settings"), callback_data="settings"),    B(T(e,"b_close"),      callback_data="close_period")],
    ])

def cancel_kb(e): return mk([[B(T(e,"b_cancel"), callback_data="cancel")]])

def confirm_kb(e, yes_data):
    return mk([[B(T(e,"b_confirm"), callback_data=yes_data), B(T(e,"b_no"), callback_data="cancel")]])

def period_kb(e, has_entries, pid):
    rows = [
        [B(T(e,"b_add"),  callback_data="add_entry"),   B(T(e,"b_pdf"),  callback_data="export_pdf")],
    ]
    if has_entries:
        rows.append([B(T(e,"b_edit_entry"), callback_data="edit_entry"),
                     B(T(e,"b_del_entry"),  callback_data="del_entry")])
    rows.append([B(T(e,"b_edit_period"), callback_data=f"edit_period:{pid}"),
                 B(T(e,"b_close"),       callback_data="close_period")])
    rows.append([B(T(e,"b_menu"), callback_data="main_menu")])
    return mk(rows)

def entries_kb(e, entries, action):
    from utils.time_utils import fmt_hours
    rows = [[B(f"📅 {en['work_date']}  ({fmt_hours(en['total_hours'])})",
               callback_data=f"{action}:{en['id']}")] for en in entries]
    rows.append([B(T(e,"b_cancel"), callback_data="cancel")])
    return mk(rows)

def periods_kb(periods):
    rows = []
    for p in periods:
        icon = "🟢" if p["is_active"] else "🔴"
        end  = p["end_date"] or "→"
        rows.append([B(f"{icon} {p['start_date']} → {end}  ({p['total_hours']:.1f}h)",
                       callback_data=f"view_period:{p['id']}")])
    rows.append([B("🏠", callback_data="main_menu")])
    return mk(rows)

def time_in_kb(e):
    return mk([
        [B("5:00 AM",callback_data="time:05:00"), B("5:30 AM",callback_data="time:05:30"), B("6:00 AM",callback_data="time:06:00")],
        [B("6:30 AM",callback_data="time:06:30"), B("7:00 AM",callback_data="time:07:00"), B("7:30 AM",callback_data="time:07:30")],
        [B("8:00 AM",callback_data="time:08:00"), B("8:30 AM",callback_data="time:08:30"), B("9:00 AM",callback_data="time:09:00")],
        [B(T(e,"b_cancel"), callback_data="cancel")],
    ])

def time_out_kb(e):
    return mk([
        [B("1:00 PM",callback_data="time:13:00"), B("1:30 PM",callback_data="time:13:30"), B("2:00 PM",callback_data="time:14:00")],
        [B("2:30 PM",callback_data="time:14:30"), B("3:00 PM",callback_data="time:15:00"), B("3:30 PM",callback_data="time:15:30")],
        [B("4:00 PM",callback_data="time:16:00"), B("4:30 PM",callback_data="time:16:30"), B("5:00 PM",callback_data="time:17:00")],
        [B(T(e,"b_cancel"), callback_data="cancel")],
    ])

def date_kb(e):
    from utils.time_utils import today
    from datetime import date, timedelta
    d = date.today()
    y1, y2 = d-timedelta(1), d-timedelta(2)
    lbl = "Hoy" if e.get("language","es")=="es" else "Today"
    return mk([
        [B(f"📅 {d.strftime('%m/%d')} ({lbl})", callback_data=f"date:{today()}"),
         B(f"📅 {y1.strftime('%m/%d')}",        callback_data=f"date:{y1.isoformat()}"),
         B(f"📅 {y2.strftime('%m/%d')}",        callback_data=f"date:{y2.isoformat()}")],
        [B(T(e,"b_cancel"), callback_data="cancel")],
    ])

def pay_kb(e):
    hr = e.get("hourly_rate"); tx = e.get("tax_percent")
    rows = [
        [B(T(e,"b_edit_rate") if hr else T(e,"b_add_rate"), callback_data="set_rate")],
        [B(T(e,"b_edit_tax")  if tx else T(e,"b_add_tax"),  callback_data="set_tax")],
    ]
    if hr: rows.append([B(T(e,"b_del_rate"), callback_data="del_rate")])
    if tx: rows.append([B(T(e,"b_del_tax"),  callback_data="del_tax")])
    rows.append([B(T(e,"b_menu"), callback_data="main_menu")])
    return mk(rows)

def settings_kb(e):
    return mk([
        [B(T(e,"b_lang"), callback_data="cfg_lang")],
        [B(T(e,"b_tfmt"), callback_data="cfg_tfmt")],
        [B(T(e,"b_dfmt"), callback_data="cfg_dfmt")],
        [B(T(e,"b_tz"),   callback_data="cfg_tz")],
        [B(T(e,"b_menu"), callback_data="main_menu")],
    ])

def lang_kb():
    return mk([[B("🇪🇸 Español",callback_data="setlang:es"), B("🇺🇸 English",callback_data="setlang:en")],
               [B("⬅️",callback_data="settings")]])

def tfmt_kb():
    return mk([[B("🕐 12h  (9:00 AM)",callback_data="settfmt:12h"), B("🕐 24h  (09:00)",callback_data="settfmt:24h")],
               [B("⬅️",callback_data="settings")]])

def dfmt_kb():
    return mk([[B("📅 MM/DD/YYYY",callback_data="setdfmt:MM/DD/YYYY")],
               [B("📅 DD/MM/YYYY",callback_data="setdfmt:DD/MM/YYYY")],
               [B("📅 YYYY-MM-DD",callback_data="setdfmt:YYYY-MM-DD")],
               [B("⬅️",callback_data="settings")]])

def tz_kb():
    zones = [("🇺🇸 Eastern (ET)","America/New_York"),("🇺🇸 Central (CT)","America/Chicago"),
             ("🇺🇸 Mountain (MT)","America/Denver"),("🇺🇸 Pacific (PT)","America/Los_Angeles"),
             ("🇲🇽 Mexico City","America/Mexico_City"),("🌎 Bogotá/Lima","America/Bogota"),
             ("🌎 Santiago","America/Santiago"),("🌎 Buenos Aires","America/Argentina/Buenos_Aires")]
    rows = [[B(lbl, callback_data=f"settz:{z}")] for lbl,z in zones]
    rows.append([B("⬅️", callback_data="settings")])
    return mk(rows)

def edit_period_kb(e, pid):
    return mk([
        [B(T(e,"b_edit_start"),  callback_data=f"ep_start:{pid}")],
        [B(T(e,"b_edit_end"),    callback_data=f"ep_end:{pid}")],
        [B(T(e,"b_edit_pnotes"),callback_data=f"ep_notes:{pid}")],
        [B(T(e,"b_reopen"),      callback_data=f"ep_reopen:{pid}")],
        [B(T(e,"b_back_hist"),   callback_data="history"),
         B(T(e,"b_menu"),        callback_data="main_menu")],
    ])
