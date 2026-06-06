from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils.keyboards import main_menu, cancel_kb
from utils.i18n import T

E = lambda u: R.get_emp(u.effective_user.id) or {}

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = R.get_emp(update.effective_user.id)
    if emp:
        await update.message.reply_text(T(emp,"welcome_back",name=emp["name"]),
            parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))
    else:
        await update.message.reply_text(T({},"welcome_new"), parse_mode=ParseMode.MARKDOWN)
        ctx.user_data["aw"] = "name"

async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    lang = emp.get("language","es")
    if lang=="en":
        txt = ("📖 *TimeSheet Bot — Commands*\n\n"
               "/add\\_entry — Add a workday\n/edit\\_entry — Edit entry\n"
               "/delete\\_entry — Delete entry\n/current\\_period — View current period\n"
               "/close\\_period — Close period\n/history — Past periods\n"
               "/export\\_pdf — Generate PDF\n/profile — Your profile\n"
               "/pay\\_settings — Pay & tax config\n/settings — Language, time, date, timezone\n"
               "/help — This message")
    else:
        txt = ("📖 *TimeSheet Bot — Comandos*\n\n"
               "/add\\_entry — Agregar día\n/edit\\_entry — Editar entrada\n"
               "/delete\\_entry — Eliminar entrada\n/current\\_period — Ver período actual\n"
               "/close\\_period — Cerrar quincena\n/history — Historial\n"
               "/export\\_pdf — Generar PDF\n/profile — Tu perfil\n"
               "/pay\\_settings — Pago y taxes\n/settings — Idioma, hora, fecha, zona horaria\n"
               "/help — Este mensaje")
    await update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

async def cb_main_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    emp = E(update)
    await q.edit_message_text(T(emp,"menu_title"), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

async def cb_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    ctx.user_data.clear()
    emp = E(update)
    await q.edit_message_text(T(emp,"cancelled"), parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))
