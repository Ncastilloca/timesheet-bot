from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils.keyboards import settings_kb, lang_kb, tfmt_kb, dfmt_kb, tz_kb
from utils.i18n import T

E = lambda u: R.get_emp(u.effective_user.id) or {}

def _txt(emp):
    lang = "Español 🇪🇸" if emp.get("language","es")=="es" else "English 🇺🇸"
    # Use HTML to avoid Markdown issues with slashes and special chars
    tz = emp.get("timezone","America/New_York")
    tfmt = emp.get("time_format","12h")
    dfmt = emp.get("date_format","MM/DD/YYYY")
    return (
        f"⚙️ <b>Configuración</b>\n\n"
        f"🌐 <b>Idioma:</b> {lang}\n"
        f"🕐 <b>Formato hora:</b> {tfmt}\n"
        f"📅 <b>Formato fecha:</b> {dfmt}\n"
        f"🌍 <b>Zona horaria:</b> {tz}"
    ) if emp.get("language","es")=="es" else (
        f"⚙️ <b>Settings</b>\n\n"
        f"🌐 <b>Language:</b> {lang}\n"
        f"🕐 <b>Time format:</b> {tfmt}\n"
        f"📅 <b>Date format:</b> {dfmt}\n"
        f"🌍 <b>Timezone:</b> {tz}"
    )

async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    if not emp:
        await update.message.reply_text(T({},"need_profile")); return
    await update.message.reply_text(_txt(emp), parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))

async def cb_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    await q.edit_message_text(_txt(emp), parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))

async def cb_cfg_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    await q.edit_message_text(
        "🌐 <b>Language / Idioma</b>\n\nChoose / Elige:",
        parse_mode=ParseMode.HTML, reply_markup=lang_kb())

async def cb_setlang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; lang = q.data.split(":")[1]; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "language", lang)
    msg = "✅ Idioma: <b>Español</b> 🇪🇸" if lang=="es" else "✅ Language: <b>English</b> 🇺🇸"
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))

async def cb_cfg_tfmt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    label = "🕐 <b>Formato de Hora</b>" if emp.get("language","es")=="es" else "🕐 <b>Time Format</b>"
    await q.edit_message_text(label, parse_mode=ParseMode.HTML, reply_markup=tfmt_kb())

async def cb_settfmt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; f = q.data.split(":")[1]; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "time_format", f)
    msg = f"✅ Formato hora: <b>{f}</b>" if emp.get("language","es")=="es" else f"✅ Time format: <b>{f}</b>"
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))

async def cb_cfg_dfmt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    label = "📅 <b>Formato de Fecha</b>" if emp.get("language","es")=="es" else "📅 <b>Date Format</b>"
    await q.edit_message_text(label, parse_mode=ParseMode.HTML, reply_markup=dfmt_kb())

async def cb_setdfmt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; f = q.data.split(":")[1]; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "date_format", f)
    msg = f"✅ Formato fecha: <b>{f}</b>" if emp.get("language","es")=="es" else f"✅ Date format: <b>{f}</b>"
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))

async def cb_cfg_tz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    label = "🌍 <b>Zona Horaria</b>" if emp.get("language","es")=="es" else "🌍 <b>Timezone</b>"
    await q.edit_message_text(label, parse_mode=ParseMode.HTML, reply_markup=tz_kb())

async def cb_settz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; z = q.data.split(":",1)[1]; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "timezone", z)
    msg = f"✅ Zona horaria: <b>{z}</b>" if emp.get("language","es")=="es" else f"✅ Timezone: <b>{z}</b>"
    await q.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=settings_kb(emp))
