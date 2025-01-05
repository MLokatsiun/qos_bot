import logging
import base64
from io import BytesIO
from telegram import Update, InputFile, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, MessageHandler, filters, CommandHandler, ConversationHandler

from api_clients import send_pdf_request_to_service

logger = logging.getLogger(__name__)

ENTERING_TG_ID = 1

async def start_search(update: Update, context: CallbackContext):
    await update.message.reply_text("Будь ласка, введіть Telegram ID для пошуку.", reply_markup=ReplyKeyboardRemove())
    return ENTERING_TG_ID

async def handle_tg_id(update: Update, context: CallbackContext):
    tg_id = update.message.text.strip()
    context.user_data["tg_id"] = tg_id

    api_key = context.user_data.get("api_key")
    if not api_key:
        await update.message.reply_text("Ви не зареєстровані або не маєте API ключа.")
        return ConversationHandler.END

    await handle_pdf_request(update, context, tg_id, api_key)

    return ConversationHandler.END

async def handle_pdf_request(update: Update, context: CallbackContext, tg_id: str, api_key: str):
    pdf_filename, pdf_base64_or_error = await send_pdf_request_to_service(tg_id, api_key)

    if pdf_filename:
        pdf_data = base64.b64decode(pdf_base64_or_error)
        pdf_file = BytesIO(pdf_data)
        pdf_file.name = f"{tg_id}.pdf"

        input_file = InputFile(pdf_file)
        await update.message.reply_document(document=input_file)
    else:
        await update.message.reply_text(f"Сталася помилка при генерації PDF: {pdf_base64_or_error}")

    keyboard = [[("Почати пошук PDF знову")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Натисніть, щоб почати пошук PDF знову:", reply_markup=reply_markup)

conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("Почати пошук"), start_search)],
    states={
        ENTERING_TG_ID: [MessageHandler(filters.TEXT, handle_tg_id)],
    },
    fallbacks=[],
)
