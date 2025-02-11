from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext):
    logger.info("Користувач %s розпочав розмову.", update.effective_user.id)

    keyboard = [[KeyboardButton("🔑 Авторизуватися", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "👋 Привіт! Для реєстрації натисни кнопку '🔑 Авторизуватися'.",
        reply_markup=reply_markup,
    )
    return 1
