from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

async def choose_search_type(update: Update):
    """Вибір типу пошуку: OSINT або Shodan."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🔎 Оберіть тип пошуку, натиснувши відповідну кнопку:",
        reply_markup=reply_markup,
    )
    return 2
