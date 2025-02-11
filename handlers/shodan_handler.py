from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

async def shodan_search(update: Update, context: CallbackContext):
    keyboard = [
        [KeyboardButton("🌐 Пошук в мережі")],
        [KeyboardButton("📁 Шукати з файлу Shodan")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🔎 Оберіть тип Shodan пошуку, натиснувши відповідну кнопку:",
        reply_markup=reply_markup,
    )
    return 4
