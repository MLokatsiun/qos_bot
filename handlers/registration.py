import logging
import re
import base64

import requests
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputFile
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, ConversationHandler
from api_clients import register_user, send_pdf_request_to_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PHONE_NUMBER = 1
START_SEARCH = 2
OFFER_SEARCH = 3

# Функція старту
async def start(update: Update, context: CallbackContext):
    logger.info("Користувач %s розпочав розмову.", update.effective_user.id)

    keyboard = [[KeyboardButton("Надіслати номер телефону", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Привіт! Натисни кнопку, щоб поділитися своїм номером телефону.",
        reply_markup=reply_markup
    )
    return PHONE_NUMBER

def save_pdf_from_base64(base64_data: str, file_path: str):
    pdf_data = base64.b64decode(base64_data)
    with open(file_path, 'wb') as f:
        f.write(pdf_data)
    return file_path


import re


def normalize_phone_number(phone_number: str) -> str:
    phone_number = re.sub(r"[^\d+]", "", phone_number)

    if phone_number.startswith("+"):
        phone_number = phone_number[1:]

    if phone_number.startswith("8"):
        phone_number = "380" + phone_number[1:]

    if phone_number.startswith("380") and len(phone_number) == 12:
        return phone_number
    return None


async def register(update: Update, context: CallbackContext):
    try:
        if update.message.contact:
            phone_number = update.message.contact.phone_number
        else:
            await update.message.reply_text(
                "Не вийшло отримати номер телефону. Переконайтесь, що ви натиснули правильну кнопку."
            )
            return PHONE_NUMBER

        normalized_phone_number = normalize_phone_number(phone_number)
        if not normalized_phone_number:
            await update.message.reply_text(
                "Номер телефону не відповідає правильному формату (+380XXXXXXXXX). Спробуйте ще раз."
            )
            return PHONE_NUMBER

        logger.info("Користувач %s намагається зареєструвати номер телефону: %s", update.effective_user.id,
                    normalized_phone_number)

        try:
            response = await register_user(normalized_phone_number)
            context.user_data["api_key"] = response.get("api_key")

            await update.message.reply_text("Ваш номер телефону успішно зареєстровано.")

            await offer_search(update)

            return ConversationHandler.END

        except ValueError as ve:
            error_message = str(ve)
            if "already exists" in error_message:
                await update.message.reply_text(
                    "Користувач з таким номером вже зареєстрований.")
                await offer_search(update)
                return ConversationHandler.END
            else:
                await update.message.reply_text(f"Сталася помилка: {error_message}")
        except requests.RequestException as e:
            await update.message.reply_text("Помилка мережі. Спробуйте пізніше.")
            logger.exception("Помилка API при реєстрації: %s", e)

    except Exception as e:
        await update.message.reply_text("Сталася непередбачена помилка. Спробуйте пізніше.")
        logger.exception("Помилка при реєстрації користувача: %s", e)

    return PHONE_NUMBER

async def handle_pdf_request(update: Update, context: CallbackContext, tg_id: str, api_key: str):
    try:
        pdf_filename, pdf_base64_or_error = await send_pdf_request_to_service(tg_id, api_key)

        if pdf_filename:
            file_path = save_pdf_from_base64(pdf_base64_or_error, f"{tg_id}_generated_pdf.pdf")
            with open(file_path, 'rb') as pdf_file:
                input_file = InputFile(pdf_file, filename="generated_pdf.pdf")
                await update.message.reply_document(document=input_file)
        else:
            await update.message.reply_text(f"Сталася помилка при генерації PDF: {pdf_base64_or_error}")

    except requests.RequestException as e:
        await update.message.reply_text("Помилка мережі під час генерації PDF. Спробуйте пізніше.")
        logger.exception("Помилка API при генерації PDF: %s", e)

    except Exception as e:
        await update.message.reply_text("Непередбачена помилка під час генерації PDF. Спробуйте пізніше.")
        logger.exception("Непередбачена помилка при генерації PDF: %s", e)

async def offer_search(update: Update):
    keyboard = [
        [KeyboardButton("Почати пошук PDF")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "Натисніть кнопку для початку пошуку PDF за вашим Telegram ID.",
        reply_markup=reply_markup
    )
    return OFFER_SEARCH


async def start_search(update: Update, context: CallbackContext):
    logger.info("Користувач %s натиснув кнопку для пошуку PDF.", update.effective_user.id)
    await update.message.reply_text("Будь ласка, введіть свій Telegram ID для пошуку PDF.")
    return START_SEARCH


async def handle_tg_id(update: Update, context: CallbackContext):
    tg_id = update.message.text
    logger.info("Отримано Telegram ID: %s", tg_id)

    api_key = context.user_data.get("api_key")
    if api_key:
        await handle_pdf_request(update, context, tg_id, api_key)
    else:
        await update.message.reply_text("Не вдалося знайти ваш API ключ. Спробуйте ще раз.")

    return ConversationHandler.END


start_handler = CommandHandler("start", start)

conversation_handler = ConversationHandler(
    entry_points=[start_handler],
    states={
        PHONE_NUMBER: [MessageHandler(filters.CONTACT, register)],
        OFFER_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_search)],
        START_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tg_id)]
    },
    fallbacks=[]
)

