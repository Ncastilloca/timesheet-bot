"""
TimeSheet Bot v4.1 - Main entry point
"""
import logging, os, sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from database.connection import init_db
from handlers.common      import cmd_start, cmd_help, cb_main_menu, cb_cancel
from handlers.profile     import (cmd_profile, cb_profile, cb_upd_name, handle_name,
                                   cmd_pay, cb_pay, cb_set_rate, cb_set_tax,
                                   cb_del_rate, cb_del_tax, handle_rate, handle_tax)
from handlers.settings    import (cmd_settings, cb_settings, cb_cfg_lang, cb_setlang,
                                   cb_cfg_tfmt, cb_settfmt, cb_cfg_dfmt, cb_setdfmt,
                                   cb_cfg_tz, cb_settz)
from handlers.entries     import (cmd_add, cb_add, cmd_edit, cb_edit, cb_ee_select, cb_ee_keepdate,
                                   cmd_del, cb_del, cb_de_select, cb_de_ok,
                                   handle_text, handle_cb)
from handlers.periods     import (cmd_period, cb_period, cmd_close, cb_close, cb_close_ok,
                                   cb_new_period, cmd_history, cb_history, cb_view_period,
                                   cb_edit_period, cb_ep_start, cb_ep_end, cb_ep_notes,
                                   cb_ep_reopen, cb_skip_ep_notes, handle_period_text)
from handlers.export      import cmd_pdf, cb_pdf, cb_pdf_period
from handlers.error_handler import handle_error

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("bot.log")],
)
logger = logging.getLogger(__name__)

ENTRY_STATES  = {"e_date","e_tin","e_tout","e_notes","ee_date","ee_tin","ee_tout","ee_notes"}
PERIOD_STATES = {"ep_start","ep_end","ep_notes"}

async def universal_text(update: Update, ctx):
    aw = ctx.user_data.get("aw")
    if   aw == "name":        await handle_name(update, ctx)
    elif aw in ENTRY_STATES:  await handle_text(update, ctx)
    elif aw in PERIOD_STATES: await handle_period_text(update, ctx)
    elif aw == "rate":        await handle_rate(update, ctx)
    elif aw == "tax":         await handle_tax(update, ctx)
    else:
        import database.repository as R
        from utils.keyboards import main_menu
        emp = R.get_emp(update.effective_user.id) or {}
        await update.message.reply_text("🏠", reply_markup=main_menu(emp))

async def universal_cb(update: Update, ctx):
    await handle_cb(update, ctx)

def build():
    load_dotenv()
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN not set in .env"); sys.exit(1)

    app = Application.builder().token(token).build()

    # ── Commands ──────────────────────────────────────────────────
    for cmd, fn in [
        ("start",          cmd_start),
        ("help",           cmd_help),
        ("profile",        cmd_profile),
        ("pay_settings",   cmd_pay),
        ("settings",       cmd_settings),
        ("add_entry",      cmd_add),
        ("edit_entry",     cmd_edit),
        ("delete_entry",   cmd_del),
        ("current_period", cmd_period),
        ("close_period",   cmd_close),
        ("history",        cmd_history),
        ("export_pdf",     cmd_pdf),
    ]:
        app.add_handler(CommandHandler(cmd, fn))

    # ── Exact callbacks ───────────────────────────────────────────
    for pattern, fn in [
        ("main_menu",     cb_main_menu),
        ("cancel",        cb_cancel),
        ("profile",       cb_profile),
        ("upd_name",      cb_upd_name),
        ("pay_settings",  cb_pay),
        ("set_rate",      cb_set_rate),
        ("set_tax",       cb_set_tax),
        ("del_rate",      cb_del_rate),
        ("del_tax",       cb_del_tax),
        ("settings",      cb_settings),
        ("cfg_lang",      cb_cfg_lang),
        ("cfg_tfmt",      cb_cfg_tfmt),
        ("cfg_dfmt",      cb_cfg_dfmt),
        ("cfg_tz",        cb_cfg_tz),
        ("add_entry",     cb_add),
        ("edit_entry",    cb_edit),
        ("del_entry",     cb_del),
        ("current_period",cb_period),
        ("close_period",  cb_close),
        ("new_period",    cb_new_period),
        ("history",       cb_history),
        ("export_pdf",    cb_pdf),
        ("skip_notes",    universal_cb),
        ("skip_ee_notes", universal_cb),
        ("skip_ep_notes", cb_skip_ep_notes),
    ]:
        app.add_handler(CallbackQueryHandler(fn, pattern=f"^{pattern}$"))

    # ── Pattern callbacks ─────────────────────────────────────────
    for pattern, fn in [
        (r"^ee:\d+$",          cb_ee_select),
        (r"^ee_keepdate:.+$",  cb_ee_keepdate),
        (r"^de:\d+$",          cb_de_select),
        (r"^de_ok:\d+$",       cb_de_ok),
        (r"^close_ok:\d+$",    cb_close_ok),
        (r"^view_period:\d+$", cb_view_period),
        (r"^edit_period:\d+$", cb_edit_period),
        (r"^ep_start:\d+$",    cb_ep_start),
        (r"^ep_end:\d+$",      cb_ep_end),
        (r"^ep_notes:\d+$",    cb_ep_notes),
        (r"^ep_reopen:\d+$",   cb_ep_reopen),
        (r"^pdf_period:\d+$",  cb_pdf_period),
        (r"^setlang:\w+$",     cb_setlang),
        (r"^settfmt:\w+$",     cb_settfmt),
        (r"^setdfmt:.+$",      cb_setdfmt),
        (r"^settz:.+$",        cb_settz),
        (r"^(date:|time:).+$", universal_cb),
    ]:
        app.add_handler(CallbackQueryHandler(fn, pattern=pattern))

    # ── Text ──────────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, universal_text))

    # ── Global error handler ──────────────────────────────────────
    app.add_error_handler(handle_error)

    return app

def main():
    init_db()
    app = build()
    logger.info("TimeSheet Bot v4.1 starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
