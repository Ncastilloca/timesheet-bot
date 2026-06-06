import io, logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils import time_utils as U
from utils.keyboards import main_menu
from utils.i18n import T

logger = logging.getLogger(__name__)
E = lambda u: R.get_emp(u.effective_user.id) or {}

async def _send(chat_id, bot, emp, p, entries):
    dfmt = emp.get("date_format","MM/DD/YYYY"); tfmt = emp.get("time_format","12h")
    try:
        from services.pdf_service import make_pdf
        pdf = make_pdf(emp["name"], p, entries, dfmt, tfmt)
        start = U.fmt_date(p["start_date"],dfmt)
        end   = U.fmt_date(p["end_date"],dfmt) if p.get("end_date") else U.today()
        total = sum(e.get("total_hours",0) or 0 for e in entries)
        fname = f"Timesheet_{emp['name'].replace(' ','_')}_{start.replace('/','_')}.pdf"
        await bot.send_document(chat_id=chat_id, document=io.BytesIO(pdf), filename=fname,
            caption=T(emp,"pdf_cap",name=emp["name"],start=start,end=end,hrs=U.fmt_hours(total)),
            parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))
    except Exception as e:
        logger.error("PDF error: %s", e, exc_info=True)
        await bot.send_message(chat_id=chat_id, text=T(emp,"pdf_err",e=str(e)),
            parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

async def cmd_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    if not emp: await update.message.reply_text(T({},"need_profile")); return
    p = R.get_active() or (R.all_periods() or [None])[0]
    if not p: await update.message.reply_text(T(emp,"pdf_empty"),reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await update.message.reply_text(T(emp,"pdf_empty"),reply_markup=main_menu(emp)); return
    await update.message.reply_text(T(emp,"pdf_wait"))
    await _send(update.message.chat_id, ctx.bot, emp, p, entries)

async def cb_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    if not emp: await q.edit_message_text(T({},"need_profile")); return
    p = R.get_active() or (R.all_periods() or [None])[0]
    if not p: await q.edit_message_text(T(emp,"pdf_empty"),reply_markup=main_menu(emp)); return
    entries = R.get_entries(p["id"])
    if not entries: await q.edit_message_text(T(emp,"pdf_empty"),reply_markup=main_menu(emp)); return
    await q.edit_message_text(T(emp,"pdf_wait"))
    await _send(q.message.chat_id, ctx.bot, emp, p, entries)

async def cb_pdf_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    pid = int(q.data.split(":")[1]); p = R.get_period(pid)
    if not p: await q.edit_message_text("⚠️ Not found."); return
    entries = R.get_entries(pid)
    if not entries: await q.edit_message_text(T(emp,"pdf_empty"),reply_markup=main_menu(emp)); return
    await q.edit_message_text(T(emp,"pdf_wait"))
    await _send(q.message.chat_id, ctx.bot, emp, p, entries)
