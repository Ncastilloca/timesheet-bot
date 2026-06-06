"""
Global error handler — sends a friendly error message with the
technical code so the user can report it easily.
"""
import html, logging, traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

async def handle_error(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch all unhandled exceptions and send them to the user."""
    # Log full traceback
    logger.error("Unhandled exception:", exc_info=ctx.error)
    tb = traceback.format_exception(None, ctx.error, ctx.error.__traceback__)
    tb_text = "".join(tb)

    # Build short error code for user to report
    error_type  = type(ctx.error).__name__
    error_short = str(ctx.error)[:200]

    message = (
        "⚠️ <b>Ocurrió un error inesperado.</b>\n\n"
        "Copia este código y compártelo para que te ayuden a resolverlo:\n\n"
        f"<pre>Tipo:    {html.escape(error_type)}\n"
        f"Detalle: {html.escape(error_short)}</pre>\n\n"
        "💡 <i>Toca /start para volver al menú principal.</i>"
    )

    # Try to send to the user
    try:
        if update and isinstance(update, Update):
            if update.callback_query:
                try:
                    await update.callback_query.answer("⚠️ Error — mira el chat", show_alert=True)
                except Exception:
                    pass
                await update.callback_query.message.reply_text(
                    message, parse_mode=ParseMode.HTML)
            elif update.message:
                await update.message.reply_text(
                    message, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Could not send error message to user: {e}")
