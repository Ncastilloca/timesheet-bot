from telegram import Update, InlineKeyboardButton as B, InlineKeyboardMarkup as K
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import database.repository as R
from utils.keyboards import main_menu, cancel_kb, pay_kb
from utils.i18n import T

E = lambda u: R.get_emp(u.effective_user.id) or {}

def _profile_kb(e):
    return K([[B(T(e,"b_change_name"), callback_data="upd_name")],
              [B(T(e,"b_pay"),         callback_data="pay_settings")],
              [B(T(e,"b_settings"),    callback_data="settings")],
              [B(T(e,"b_menu"),        callback_data="main_menu")]])

def _pay_txt(e):
    r = e.get("hourly_rate"); t = e.get("tax_percent")
    return T(e,"pay_title",
             rate=T(e,"rate_set",r=r) if r else T(e,"rate_none"),
             tax=T(e,"tax_set",t=t)   if t else T(e,"tax_none"))

async def cmd_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    if not emp:
        ctx.user_data["aw"] = "name"
        await update.message.reply_text(T({},"ask_name"), parse_mode=ParseMode.MARKDOWN); return
    await update.message.reply_text(
        T(emp,"profile_text",name=emp["name"],since=emp["created_at"][:10]),
        parse_mode=ParseMode.MARKDOWN, reply_markup=_profile_kb(emp))

async def cb_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    emp = E(update)
    if not emp:
        ctx.user_data["aw"] = "name"
        await q.edit_message_text(T({},"ask_name"), parse_mode=ParseMode.MARKDOWN); return
    await q.edit_message_text(
        T(emp,"profile_text",name=emp["name"],since=emp["created_at"][:10]),
        parse_mode=ParseMode.MARKDOWN, reply_markup=_profile_kb(emp))

async def cb_upd_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    emp = E(update); ctx.user_data["aw"] = "name"
    await q.edit_message_text(T(emp,"ask_name"), parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb(emp))

async def handle_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 2:
        emp = E(update)
        await update.message.reply_text(T(emp,"name_short"), reply_markup=cancel_kb(emp)); return
    emp = R.upsert_emp(update.effective_user.id, name)
    ctx.user_data.pop("aw", None)
    await update.message.reply_text(T(emp,"name_saved",name=emp["name"]),
        parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu(emp))

async def cmd_pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    if not emp: await update.message.reply_text(T({},"need_profile")); return
    await update.message.reply_text(_pay_txt(emp), parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))

async def cb_pay(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    if not emp: await q.edit_message_text(T({},"need_profile")); return
    await q.edit_message_text(_pay_txt(emp), parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))

async def cb_set_rate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    ctx.user_data["aw"] = "rate"
    await q.edit_message_text(T(emp,"ask_rate"), parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb(emp))

async def cb_set_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); emp = E(update)
    ctx.user_data["aw"] = "tax"
    await q.edit_message_text(T(emp,"ask_tax"), parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb(emp))

async def cb_del_rate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "hourly_rate", None)
    await q.edit_message_text(T(emp,"rate_del")+"\n\n"+_pay_txt(emp),
        parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))

async def cb_del_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    emp = R.set_emp_field(update.effective_user.id, "tax_percent", None)
    await q.edit_message_text(T(emp,"tax_del")+"\n\n"+_pay_txt(emp),
        parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))

async def handle_rate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    try:
        v = float(update.message.text.strip().replace("$","").replace(",",""))
        if v <= 0: raise ValueError
    except:
        await update.message.reply_text(T(emp,"bad_number"), parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb(emp)); return
    emp = R.set_emp_field(update.effective_user.id, "hourly_rate", v)
    ctx.user_data.pop("aw", None)
    await update.message.reply_text(T(emp,"rate_ok",r=v)+"\n\n"+_pay_txt(emp),
        parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))

async def handle_tax(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    emp = E(update)
    try:
        v = float(update.message.text.strip().replace("%",""))
        if not (0 < v < 100): raise ValueError
    except:
        await update.message.reply_text(T(emp,"bad_percent"), parse_mode=ParseMode.MARKDOWN, reply_markup=cancel_kb(emp)); return
    emp = R.set_emp_field(update.effective_user.id, "tax_percent", v)
    ctx.user_data.pop("aw", None)
    await update.message.reply_text(T(emp,"tax_ok",t=v)+"\n\n"+_pay_txt(emp),
        parse_mode=ParseMode.MARKDOWN, reply_markup=pay_kb(emp))
