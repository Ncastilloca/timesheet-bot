from telegram import Update, InlineKeyboardButton as B, InlineKeyboardMarkup as K
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils import time_utils as U
from utils.keyboards import main_menu, confirm_kb, period_kb, periods_kb, edit_period_kb, cancel_kb
from utils.i18n import T

E = lambda u: R.get_emp(u.effective_user.id) or {}

def _earn(emp, hrs):
    rate = emp.get("hourly_rate")
    if not rate: return ""
    tax = emp.get("tax_percent"); gross = hrs * rate
    out = T(emp,"gross",g=gross)
    if tax:
        ded = gross*(tax/100)
        out += T(emp,"tax_line",p=tax,d=ded) + T(emp,"net",n=gross-ded)
    return out

def _period_text(emp, p, entries):
    dfmt = emp.get("date_format","MM/DD/YYYY"); tfmt = emp.get("time_format","12h")
    start = U.fmt_date(p["start_date"],dfmt)
    end   = U.fmt_date(p["end_date"],dfmt) if p.get("end_date") else T(emp,"today")
    status = T(emp,"active") if p["is_active"] else T(emp,"closed")
    total  = sum(e.get("total_hours",0) or 0 for e in entries)
    if not entries:
        table = "  _" + T(emp,"no_entries") + "_"
    else:
        rows = []
        for e in entries:
            rows.append(f"  • `{U.fmt_date(e['work_date'],dfmt)}` {U.day_abbr(e['work_date'],emp.get('language','es'))}"
                        f"  {U.fmt_time(e['time_in'],tfmt)} → {U.fmt_time(e['time_out'],tfmt)}"
                        f"  *{U.fmt_hours(e['total_hours'])}*")
        table = "\n".join(rows)
    return T(emp,"period_body", id=p["id"], start=start, end=end, status=status,
             table=table, days=len(entries), hfmt=U.fmt_hours(total),
             hdec=f"{total:.2f}", earn=_earn(emp,total))

# ── CURRENT PERIOD ────────────────────────────────────────────────

async def cmd_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update); p = R.get_active()
    if not p:
        await update.message.reply_text(T(emp,"no_period"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_new_period"),callback_data="new_period"),B(T(emp,"b_menu"),callback_data="main_menu")]])); return
    entries = R.get_entries(p["id"])
    await update.message.reply_text(_period_text(emp,p,entries),
        parse_mode=ParseMode.MARKDOWN, reply_markup=period_kb(emp,bool(entries),p["id"]))

async def cb_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update); p = R.get_active()
    if not p:
        await q.edit_message_text(T(emp,"no_period"), parse_mode=ParseMode.MARKDOWN,
            reply_markup=K([[B(T(emp,"b_new_period"),callback_data="new_period"),B(T(emp,"b_menu"),callback_data="main_menu")]])); return
    entries = R.get_entries(p["id"])
    await q.edit_message_text(_period_text(emp,p,entries),
        parse_mode=ParseMode.MARKDOWN, reply_markup=period_kb(emp,bool(entries),p["id"]))

# ── CLOSE PERIOD ──────────────────────────────────────────────────

async def cmd_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update); p = R.get_active()
    if not p: await update.message.reply_text("⚠️ "+T(emp,"no_period"),reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"]); total = sum(e.get("total_hours",0) or 0 for e in entries)
    dfmt = emp.get("date_format","MM/DD/YYYY")
    await update.message.reply_text(
        T(emp,"confirm_close",start=U.fmt_date(p["start_date"],dfmt),
          end=U.fmt_date(U.today(),dfmt),days=len(entries),hrs=U.fmt_hours(total)),
        parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_kb(emp,f"close_ok:{p['id']}"))

async def cb_close(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update); p = R.get_active()
    if not p: await q.edit_message_text("⚠️ "+T(emp,"no_period"),reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"]); total = sum(e.get("total_hours",0) or 0 for e in entries)
    dfmt = emp.get("date_format","MM/DD/YYYY")
    await q.edit_message_text(
        T(emp,"confirm_close",start=U.fmt_date(p["start_date"],dfmt),
          end=U.fmt_date(U.today(),dfmt),days=len(entries),hrs=U.fmt_hours(total)),
        parse_mode=ParseMode.MARKDOWN, reply_markup=confirm_kb(emp,f"close_ok:{p['id']}"))

async def cb_close_ok(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1]); p = R.get_period(pid)
    if not p or not p["is_active"]: await q.edit_message_text("⚠️ Already closed."); return
    entries = R.get_entries(pid); total = sum(e.get("total_hours",0) or 0 for e in entries)
    end = U.today(); R.close_period(pid, end, total)
    dfmt = emp.get("date_format","MM/DD/YYYY")
    await q.edit_message_text(
        T(emp,"closed_ok",id=pid,start=U.fmt_date(p["start_date"],dfmt),end=U.fmt_date(end,dfmt),
          days=len(entries),hrs=U.fmt_hours(total),dec=f"{total:.2f}",earn=_earn(emp,total)),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=K([[B(T(emp,"b_new_period"),callback_data="new_period"),
                         B(T(emp,"b_pdf"),       callback_data=f"pdf_period:{pid}")],
                        [B(T(emp,"b_menu"),       callback_data="main_menu")]]))

# ── NEW PERIOD ────────────────────────────────────────────────────

async def cb_new_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    active = R.get_active()
    if active:
        await q.edit_message_text(T(emp,"already_open",id=active["id"]),reply_markup=main_menu(emp)); return
    p = R.create_period(U.today()); dfmt = emp.get("date_format","MM/DD/YYYY")
    await q.edit_message_text(T(emp,"new_ok",date=U.fmt_date(U.today(),dfmt),id=p["id"]),
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

# ── HISTORY ───────────────────────────────────────────────────────

async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update); ps = R.all_periods()
    if not ps: await update.message.reply_text(T(emp,"no_hist"),reply_markup=main_menu(emp)); return
    await update.message.reply_text(T(emp,"hist_title"),parse_mode=ParseMode.MARKDOWN,reply_markup=periods_kb(ps))

async def cb_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update); ps = R.all_periods()
    if not ps: await q.edit_message_text(T(emp,"no_hist"),reply_markup=main_menu(emp)); return
    await q.edit_message_text(T(emp,"hist_title"),parse_mode=ParseMode.MARKDOWN,reply_markup=periods_kb(ps))

async def cb_view_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1]); p = R.get_period(pid)
    if not p: await q.edit_message_text("⚠️ Not found."); return
    entries = R.get_entries(pid)
    rows = [[B(T(emp,"b_pdf"),callback_data=f"pdf_period:{pid}")],
            [B(T(emp,"b_edit_period"),callback_data=f"edit_period:{pid}")]]
    if p["is_active"] and entries:
        rows.insert(1,[B(T(emp,"b_edit_entry"),callback_data="edit_entry"),
                       B(T(emp,"b_del_entry"), callback_data="del_entry")])
    rows += [[B(T(emp,"b_back_hist"),callback_data="history"),B(T(emp,"b_menu"),callback_data="main_menu")]]
    await q.edit_message_text(_period_text(emp,p,entries),parse_mode=ParseMode.MARKDOWN,reply_markup=K(rows))

# ── EDIT PERIOD ───────────────────────────────────────────────────

async def cb_edit_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1]); p = R.get_period(pid)
    if not p: await q.edit_message_text("⚠️ Not found."); return
    dfmt = emp.get("date_format","MM/DD/YYYY")
    await q.edit_message_text(
        T(emp,"edit_period_title", id=pid,
          start=U.fmt_date(p["start_date"],dfmt),
          end=U.fmt_date(p["end_date"],dfmt) if p.get("end_date") else "—",
          notes=p.get("notes") or "—"),
        parse_mode=ParseMode.MARKDOWN, reply_markup=edit_period_kb(emp,pid))

async def cb_ep_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1])
    ctx.user_data.update({"aw":"ep_start","ep_pid":pid})
    await q.edit_message_text(T(emp,"ask_pstart"),parse_mode=ParseMode.MARKDOWN,reply_markup=cancel_kb(emp))

async def cb_ep_end(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1])
    ctx.user_data.update({"aw":"ep_end","ep_pid":pid})
    await q.edit_message_text(T(emp,"ask_pend"),parse_mode=ParseMode.MARKDOWN,reply_markup=cancel_kb(emp))

async def cb_ep_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1])
    ctx.user_data.update({"aw":"ep_notes","ep_pid":pid})
    kb = K([[B(T(emp,"b_skip"),callback_data="skip_ep_notes"),B(T(emp,"b_cancel"),callback_data="cancel")]])
    await q.edit_message_text(T(emp,"ask_pnotes"),parse_mode=ParseMode.MARKDOWN,reply_markup=kb)

async def cb_ep_reopen(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1])
    active = R.get_active()
    if active and active["id"] != pid:
        await q.edit_message_text(T(emp,"already_open",id=active["id"]),reply_markup=main_menu(emp)); return
    R.reopen_period(pid)
    await q.edit_message_text(T(emp,"reopen_ok",id=pid),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))

async def cb_skip_ep_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = ctx.user_data.get("ep_pid")
    if pid: R.update_period(pid, notes="")
    ctx.user_data.clear()
    await q.edit_message_text(T(emp,"period_updated"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))

async def handle_period_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    aw = ctx.user_data.get("aw"); emp = E(update); txt = update.message.text.strip()
    pid = ctx.user_data.get("ep_pid")
    dfmt = emp.get("date_format","MM/DD/YYYY")
    if aw == "ep_start":
        d = U.parse_date(txt)
        if not d: await update.message.reply_text(T(emp,"err_date"),parse_mode=ParseMode.MARKDOWN,reply_markup=cancel_kb(emp)); return
        R.update_period(pid, start_date=U.store_date(d))
        ctx.user_data.clear()
        await update.message.reply_text(T(emp,"period_updated"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))
    elif aw == "ep_end":
        d = U.parse_date(txt)
        if not d: await update.message.reply_text(T(emp,"err_date"),parse_mode=ParseMode.MARKDOWN,reply_markup=cancel_kb(emp)); return
        R.update_period(pid, end_date=U.store_date(d))
        ctx.user_data.clear()
        await update.message.reply_text(T(emp,"period_updated"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))
    elif aw == "ep_notes":
        R.update_period(pid, notes=txt)
        ctx.user_data.clear()
        await update.message.reply_text(T(emp,"period_updated"),parse_mode=ParseMode.MARKDOWN,reply_markup=main_menu(emp))
