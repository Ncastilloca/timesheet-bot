from telegram import Update, InlineKeyboardButton as B, InlineKeyboardMarkup as K
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils import time_utils as U
from utils.keyboards import cancel_kb, confirm_kb, entries_kb, time_in_kb, time_out_kb, date_kb, main_menu
from utils.i18n import T

E = lambda u: R.get_emp(u.effective_user.id) or {}

# ── ADD ───────────────────────────────────────────────────────────

async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    if not emp: await update.message.reply_text(T({},"need_profile")); return
    p = R.get_active()
    if not p:
        await update.message.reply_text(T(emp,"no_period"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_new_period"),callback_data="new_period"),B(T(emp,"b_cancel"),callback_data="cancel")]])); return
    ctx.user_data.update({"aw":"e_date","pid":p["id"]})
    await update.message.reply_text(T(emp,"ask_date"), parse_mode=ParseMode.MARKDOWN, reply_markup=date_kb(emp))

async def cb_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    if not emp: await q.edit_message_text(T({},"need_profile")); return
    p = R.get_active()
    if not p:
        await q.edit_message_text(T(emp,"no_period"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_new_period"),callback_data="new_period"),B(T(emp,"b_cancel"),callback_data="cancel")]])); return
    ctx.user_data.update({"aw":"e_date","pid":p["id"]})
    await q.edit_message_text(T(emp,"ask_date"), parse_mode=ParseMode.MARKDOWN, reply_markup=date_kb(emp))

# ── EDIT ENTRY ────────────────────────────────────────────────────

async def cmd_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update); p = R.get_active()
    if not p: await update.message.reply_text(T(emp,"no_period"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await update.message.reply_text(T(emp,"no_entries"),reply_markup=main_menu(emp)); return
    await update.message.reply_text(T(emp,"pick_edit"), parse_mode=ParseMode.MARKDOWN, reply_markup=entries_kb(emp,entries,"ee"))

async def cb_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update); p = R.get_active()
    if not p: await q.edit_message_text(T(emp,"no_period"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await q.edit_message_text(T(emp,"no_entries"),reply_markup=main_menu(emp)); return
    await q.edit_message_text(T(emp,"pick_edit"), parse_mode=ParseMode.MARKDOWN, reply_markup=entries_kb(emp,entries,"ee"))

async def cb_ee_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    eid = int(q.data.split(":")[1]); en = R.get_entry(eid)
    if not en: await q.edit_message_text("⚠️ Not found."); return
    tfmt = emp.get("time_format","12h"); dfmt = emp.get("date_format","MM/DD/YYYY")
    ctx.user_data.update({"aw":"ee_date","ee_id":eid,"ee_pid":en["period_id"],"ee_old_date":en["work_date"]})
    await q.edit_message_text(
        f"✏️ *{U.fmt_date(en['work_date'],dfmt)}*\n"
        f"Actual: {U.fmt_time(en['time_in'],tfmt)} → {U.fmt_time(en['time_out'],tfmt)}\n\n"
        f"📅 Nueva fecha o toca Continuar con la misma:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=K([
            [B(f"📅 Misma fecha ({U.fmt_date(en['work_date'],dfmt)})", callback_data=f"ee_keepdate:{en['work_date']}")],
            [B(T(emp,"b_cancel"), callback_data="cancel")]
        ]))

async def cb_ee_keepdate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    date = q.data.split(":")[1]
    ctx.user_data["ee_date"] = date
    ctx.user_data["aw"] = "ee_tin"
    await q.edit_message_text(T(emp,"ask_tin"), parse_mode=ParseMode.MARKDOWN, reply_markup=time_in_kb(emp))

# ── DELETE ENTRY ──────────────────────────────────────────────────

async def cmd_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update); p = R.get_active()
    if not p: await update.message.reply_text(T(emp,"no_period"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await update.message.reply_text(T(emp,"no_entries"),reply_markup=main_menu(emp)); return
    await update.message.reply_text(T(emp,"pick_del"), parse_mode=ParseMode.MARKDOWN, reply_markup=entries_kb(emp,entries,"de"))

async def cb_del(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update); p = R.get_active()
    if not p: await q.edit_message_text(T(emp,"no_period"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await q.edit_message_text(T(emp,"no_entries"),reply_markup=main_menu(emp)); return
    await q.edit_message_text(T(emp,"pick_del"), parse_mode=ParseMode.MARKDOWN, reply_markup=entries_kb(emp,entries,"de"))

async def cb_de_select(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    eid = int(q.data.split(":")[1]); en = R.get_entry(eid)
    if not en: await q.edit_message_text("⚠️ Not found."); return
    tfmt = emp.get("time_format","12h"); dfmt = emp.get("date_format","MM/DD/YYYY")
    await q.edit_message_text(
        T(emp,"confirm_del",date=U.fmt_date(en["work_date"],dfmt),
          tin=U.fmt_time(en["time_in"],tfmt),tout=U.fmt_time(en["time_out"],tfmt),
          hrs=U.fmt_hours(en["total_hours"])),
        parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_kb(emp,f"de_ok:{eid}"))

async def cb_de_ok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    eid = int(q.data.split(":")[1]); en = R.get_entry(eid)
    if not en: await q.edit_message_text("⚠️ Not found."); return
    pid = en["period_id"]; R.delete_entry(eid); total = R.recalc(pid)
    ctx.user_data.clear()
    await q.edit_message_text(T(emp,"entry_deleted",total=U.fmt_hours(total)),
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

# ── TEXT ROUTER ───────────────────────────────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aw = ctx.user_data.get("aw"); emp = E(update); txt = update.message.text.strip()
    if   aw == "e_date":  await _e_date(update, ctx, emp, txt)
    elif aw == "e_tin":   await _e_tin(update, ctx, emp, txt)
    elif aw == "e_tout":  await _e_tout(update, ctx, emp, txt)
    elif aw == "e_notes": await _fin_add(update, ctx, emp, txt, "msg")
    elif aw == "ee_date": await _ee_date(update, ctx, emp, txt)
    elif aw == "ee_tin":  await _ee_tin(update, ctx, emp, txt)
    elif aw == "ee_tout": await _ee_tout(update, ctx, emp, txt)
    elif aw == "ee_notes":await _fin_edit(update, ctx, emp, txt, "msg")

async def handle_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; d = q.data; aw = ctx.user_data.get("aw"); emp = E(update)
    if d.startswith("date:"):
        ds = d.split(":",1)[1]; ctx.user_data["e_date"] = ds; ctx.user_data["aw"] = "e_tin"
        await q.answer()
        await q.edit_message_text(
            f"📅 {U.fmt_date(ds,emp.get('date_format','MM/DD/YYYY'))}\n\n{T(emp,'ask_tin')}",
            parse_mode=ParseMode.MARKDOWN, reply_markup=time_in_kb(emp))
    elif d.startswith("time:") and aw in ("e_tin","e_tout","ee_tin","ee_tout"):
        await _time_btn(update, ctx, emp, d.split(":",1)[1])
    elif d == "skip_notes":
        await q.answer(); await _fin_add(update, ctx, emp, "", "cb")
    elif d == "skip_ee_notes":
        await q.answer(); await _fin_edit(update, ctx, emp, "", "cb")

# ── ADD STEPS ─────────────────────────────────────────────────────

async def _e_date(update, ctx, emp, txt):
    d = U.parse_date(txt)
    if not d: await update.message.reply_text(T(emp,"err_date"),parse_mode=ParseMode.MARKDOWN,reply_markup=date_kb(emp)); return
    ctx.user_data["e_date"] = U.store_date(d); ctx.user_data["aw"] = "e_tin"
    await update.message.reply_text(
        f"📅 {U.fmt_date(U.store_date(d),emp.get('date_format','MM/DD/YYYY'))}\n\n{T(emp,'ask_tin')}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=time_in_kb(emp))

async def _e_tin(update, ctx, emp, txt):
    dt = U.parse_time(txt)
    if not dt: await update.message.reply_text(T(emp,"err_time"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_in_kb(emp)); return
    ctx.user_data["e_tin"] = U.store_time(dt); ctx.user_data["aw"] = "e_tout"
    await update.message.reply_text(
        f"🕐 {U.fmt_time(U.store_time(dt),emp.get('time_format','12h'))}\n\n{T(emp,'ask_tout')}",
        parse_mode=ParseMode.MARKDOWN, reply_markup=time_out_kb(emp))

async def _e_tout(update, ctx, emp, txt):
    dt = U.parse_time(txt)
    if not dt: await update.message.reply_text(T(emp,"err_time"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_out_kb(emp)); return
    tout = U.store_time(dt); hrs = U.calc_hours(ctx.user_data["e_tin"], tout)
    if hrs is None: await update.message.reply_text(T(emp,"err_range"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_out_kb(emp)); return
    ctx.user_data["e_tout"] = tout; ctx.user_data["e_hrs"] = hrs; ctx.user_data["aw"] = "e_notes"
    tfmt = emp.get("time_format","12h")
    await update.message.reply_text(
        f"🕔 {U.fmt_time(tout,tfmt)}  ⏱️ *{U.fmt_hours(hrs)}*\n\n{T(emp,'ask_notes')}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=K([[B(T(emp,"b_skip"),callback_data="skip_notes"),B(T(emp,"b_cancel"),callback_data="cancel")]]))

async def _fin_add(src, ctx, emp, notes, via):
    """via='msg' or via='cb' — avoids the freeze bug"""
    ud = ctx.user_data
    pid = ud["pid"]; date = ud["e_date"]; tin = ud["e_tin"]; tout = ud["e_tout"]; hrs = ud["e_hrs"]
    tfmt = emp.get("time_format","12h"); dfmt = emp.get("date_format","MM/DD/YYYY")
    if R.entry_by_date(pid, date):
        ctx.user_data.clear()
        msg = T(emp,"err_dup",date=U.fmt_date(date,dfmt))
        if via=="cb": await src.callback_query.edit_message_text(msg,parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))
        else:         await src.message.reply_text(msg,parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))
        return
    R.create_entry(pid, date, tin, tout, hrs, notes)
    total = R.recalc(pid); entries = R.get_entries(pid)
    log = ""
    for en in entries:
        log += f"  • `{U.fmt_date(en['work_date'],dfmt)}` {U.day_abbr(en['work_date'],emp.get('language','es'))}  {U.fmt_time(en['time_in'],tfmt)} → {U.fmt_time(en['time_out'],tfmt)}  *{U.fmt_hours(en['total_hours'])}*\n"
    ctx.user_data.clear()
    text = T(emp,"entry_ok",date=U.fmt_date(date,dfmt),tin=U.fmt_time(tin,tfmt),
             tout=U.fmt_time(tout,tfmt),hrs=U.fmt_hours(hrs),total=U.fmt_hours(total),days=len(entries),log=log)
    kb = K([[B(T(emp,"b_add_more"),callback_data="add_entry"),B(T(emp,"b_view"),callback_data="current_period")],
            [B(T(emp,"b_menu"),callback_data="main_menu")]])
    if via=="cb": await src.callback_query.edit_message_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=kb)
    else:         await src.message.reply_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=kb)

# ── EDIT ENTRY STEPS ──────────────────────────────────────────────

async def _ee_date(update, ctx, emp, txt):
    d = U.parse_date(txt)
    if not d: await update.message.reply_text(T(emp,"err_date"),parse_mode=ParseMode.MARKDOWN,reply_markup=date_kb(emp)); return
    ctx.user_data["ee_date"] = U.store_date(d); ctx.user_data["aw"] = "ee_tin"
    await update.message.reply_text(T(emp,"ask_tin"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_in_kb(emp))

async def _ee_tin(update, ctx, emp, txt):
    dt = U.parse_time(txt)
    if not dt: await update.message.reply_text(T(emp,"err_time"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_in_kb(emp)); return
    ctx.user_data["ee_tin"] = U.store_time(dt); ctx.user_data["aw"] = "ee_tout"
    await update.message.reply_text(T(emp,"ask_tout"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_out_kb(emp))

async def _ee_tout(update, ctx, emp, txt):
    dt = U.parse_time(txt)
    if not dt: await update.message.reply_text(T(emp,"err_time"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_out_kb(emp)); return
    tout = U.store_time(dt); hrs = U.calc_hours(ctx.user_data["ee_tin"], tout)
    if hrs is None: await update.message.reply_text(T(emp,"err_range"),parse_mode=ParseMode.MARKDOWN,reply_markup=time_out_kb(emp)); return
    ctx.user_data["ee_tout"] = tout; ctx.user_data["ee_hrs"] = hrs; ctx.user_data["aw"] = "ee_notes"
    tfmt = emp.get("time_format","12h")
    await update.message.reply_text(
        f"🕔 {U.fmt_time(tout,tfmt)}  ⏱️ *{U.fmt_hours(hrs)}*\n\n{T(emp,'ask_notes')}",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=K([[B(T(emp,"b_skip"),callback_data="skip_ee_notes"),B(T(emp,"b_cancel"),callback_data="cancel")]]))

async def _fin_edit(src, ctx, emp, notes, via):
    ud = ctx.user_data
    eid = ud["ee_id"]; date = ud["ee_date"]; tin = ud["ee_tin"]; tout = ud["ee_tout"]; hrs = ud["ee_hrs"]
    tfmt = emp.get("time_format","12h"); dfmt = emp.get("date_format","MM/DD/YYYY")
    en = R.update_entry(eid, date, tin, tout, hrs, notes)
    total = R.recalc(en["period_id"])
    ctx.user_data.clear()
    text = T(emp,"entry_updated",date=U.fmt_date(date,dfmt),tin=U.fmt_time(tin,tfmt),
             tout=U.fmt_time(tout,tfmt),hrs=U.fmt_hours(hrs),total=U.fmt_hours(total))
    kb = K([[B(T(emp,"b_view"),callback_data="current_period"),B(T(emp,"b_menu"),callback_data="main_menu")]])
    if via=="cb": await src.callback_query.edit_message_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=kb)
    else:         await src.message.reply_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=kb)

# ── TIME BUTTON ───────────────────────────────────────────────────

async def _time_btn(update, ctx, emp, tv):
    q = update.callback_query; aw = ctx.user_data.get("aw"); tfmt = emp.get("time_format","12h")
    if aw == "e_tin":
        ctx.user_data["e_tin"] = tv; ctx.user_data["aw"] = "e_tout"; await q.answer()
        await q.edit_message_text(f"🕐 *{U.fmt_time(tv,tfmt)}*\n\n{T(emp,'ask_tout')}",
            parse_mode=ParseMode.MARKDOWN, reply_markup=time_out_kb(emp))
    elif aw == "e_tout":
        hrs = U.calc_hours(ctx.user_data["e_tin"], tv)
        if hrs is None: await q.answer(T(emp,"err_range"), show_alert=True); return
        ctx.user_data["e_tout"]=tv; ctx.user_data["e_hrs"]=hrs; ctx.user_data["aw"]="e_notes"; await q.answer()
        await q.edit_message_text(
            f"🕔 *{U.fmt_time(tv,tfmt)}*  ⏱️ *{U.fmt_hours(hrs)}*\n\n{T(emp,'ask_notes')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_skip"),callback_data="skip_notes"),B(T(emp,"b_cancel"),callback_data="cancel")]]))
    elif aw == "ee_tin":
        ctx.user_data["ee_tin"]=tv; ctx.user_data["aw"]="ee_tout"; await q.answer()
        await q.edit_message_text(f"🕐 *{U.fmt_time(tv,tfmt)}*\n\n{T(emp,'ask_tout')}",
            parse_mode=ParseMode.MARKDOWN, reply_markup=time_out_kb(emp))
    elif aw == "ee_tout":
        hrs = U.calc_hours(ctx.user_data["ee_tin"], tv)
        if hrs is None: await q.answer(T(emp,"err_range"), show_alert=True); return
        ctx.user_data["ee_tout"]=tv; ctx.user_data["ee_hrs"]=hrs; ctx.user_data["aw"]="ee_notes"; await q.answer()
        await q.edit_message_text(
            f"🕔 *{U.fmt_time(tv,tfmt)}*  ⏱️ *{U.fmt_hours(hrs)}*\n\n{T(emp,'ask_notes')}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_skip"),callback_data="skip_ee_notes"),B(T(emp,"b_cancel"),callback_data="cancel")]]))
