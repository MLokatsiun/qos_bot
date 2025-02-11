from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

async def osint_search(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("🌟 Почати пошук")],
        [KeyboardButton("📁 Шукати з файлу")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🔎 Оберіть тип OSINT пошуку, натиснувши відповідну кнопку:",
        reply_markup=reply_markup,
    )
    return 3
