import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler
from api_clients import send_request_to_api
from handlers.search_handler import choose_search_type

logger = logging.getLogger(__name__)

ENTERING_COUNTRY, ENTERING_SEARCH_TYPE, ENTERING_SEARCH_DATA = range(3)

async def main_menu(update: Update, context: CallbackContext):
    """Головне меню з кнопками для вибору."""
    keyboard = [
        [KeyboardButton("🌟 Почати пошук")],
        [KeyboardButton("📁 Шукати з файлу")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("👋 Привіт! Оберіть дію:", reply_markup=reply_markup)


async def osint_shodan_menu(update: Update, context: CallbackContext):
    """Меню з кнопками OSINT та Shodan."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🔍 Оберіть інструмент:", reply_markup=reply_markup)


async def start_search(update: Update, context: CallbackContext):
    """Запуск процесу пошуку."""
    await update.message.reply_text("🚀 Будь ласка, почніть пошук.", reply_markup=ReplyKeyboardRemove())
    tg_id = str(update.message.from_user.id)
    context.user_data["tg_id"] = tg_id
    api_key = context.user_data.get("api_key")

    if not api_key:
        keyboard = [[KeyboardButton("🔑 Авторизуватися")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "❗ Ви не зареєстровані або не маєте API ключа. Щоб продовжити, натисніть кнопку для авторизації.",
            reply_markup=reply_markup)
        return ConversationHandler.END

    keyboard = [
        [KeyboardButton("🇺🇦 Україна"), KeyboardButton("🇷🇺 Росія")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🌍 Виберіть країну для пошуку:", reply_markup=reply_markup)
    return ENTERING_COUNTRY


async def handle_country(update: Update, context: CallbackContext):
    """Обробка вибору країни."""
    country = update.message.text.strip()

    if country == "🔙 Назад":
        await main_menu(update, context)
        return ConversationHandler.END

    if country == "🏠 Головне меню":
        await osint_shodan_menu(update, context)
        return ConversationHandler.END

    country_mapping = {
        "🇺🇦 Україна": "UA",
        "🇷🇺 Росія": "RU"
    }

    if country in country_mapping:
        context.user_data["country"] = country_mapping[country]  # Зберігаємо код країни
        keyboard = [
            [KeyboardButton("🔍 Шукати по Telegram ID"),
             KeyboardButton("📱 Шукати по телефону"),
             KeyboardButton("👤 Шукати по ФІО")],
            [KeyboardButton("🌍 Змінити країну пошуку"), KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Виберіть, як шукати:", reply_markup=reply_markup)
        return ENTERING_SEARCH_TYPE
    else:
        await update.message.reply_text("❌ Будь ласка, виберіть коректну країну для пошуку.")
        return ENTERING_COUNTRY


async def handle_request_data(update: Update, context: CallbackContext):
    """Обробка запиту за введеними даними."""
    search_data = update.message.text.strip()
    search_type = context.user_data.get("search_type")
    country = context.user_data.get("country")
    tg_id = context.user_data.get("tg_id")
    api_key = context.user_data.get("api_key")

    if update.message.text == "🔙 Назад":
        await main_menu(update, context)
        return ConversationHandler.END

    if update.message.text == "🏠 Головне меню":
        await osint_shodan_menu(update, context)
        return ConversationHandler.END

    if update.message.text == "🌍 Змінити країну пошуку":
        keyboard = [
            [KeyboardButton("🇺🇦 Україна"), KeyboardButton("🇷🇺 Росія")],
            [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("🌍 Виберіть країну для пошуку:", reply_markup=reply_markup)
        return ENTERING_COUNTRY

    if not tg_id or not api_key:
        keyboard = [[KeyboardButton("🔑 Авторизуватися")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "❗ Ви не зареєстровані або не маєте API ключа. Щоб продовжити, натисніть кнопку для авторизації.",
            reply_markup=reply_markup)
        return ConversationHandler.END

    response = await send_request_to_api(tg_id, search_data, search_type, api_key, country)

    if response.get("error"):
        await update.message.reply_text(f"❌ Сталася помилка при пошуку: {response['error']}")
    else:
        request_ids = ", ".join(response.get("request_ids", []))
        await update.message.reply_text(f"✅ Запит успішно надіслано.\n\nRequest IDs: {request_ids}")

    keyboard = [
        [KeyboardButton("🔍 Шукати по Telegram ID"),
         KeyboardButton("📱 Шукати по телефону"),
         KeyboardButton("👤 Шукати по ФІО")],
        [KeyboardButton("🌍 Змінити країну пошуку"), KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("Оберіть, що робити далі:", reply_markup=reply_markup)

    return ENTERING_SEARCH_TYPE


async def handle_search_type(update: Update, context: CallbackContext):
    """Обробка вибору типу пошуку."""
    search_type = update.message.text.strip().lower()

    if search_type == '🔍 шукати по telegram id':
        await update.message.reply_text("🔍 Будь ласка, введіть Telegram ID для пошуку.")
        context.user_data["search_type"] = "#"
    elif search_type == '📱 шукати по телефону':
        await update.message.reply_text("📱 Будь ласка, введіть номер телефону для пошуку.")
        context.user_data["search_type"] = "PHONE"
    elif search_type == '👤 шукати по фіо':
        await update.message.reply_text("👤 Будь ласка, введіть ФІО для пошуку.")
        context.user_data["search_type"] = "FIO"
    elif search_type == '🔙 назад':
        await main_menu(update, context)
        return ConversationHandler.END
    elif search_type == '🏠 головне меню':
        await osint_shodan_menu(update, context)
        return ConversationHandler.END
    elif search_type == '🌍 змінити країну пошуку':
        keyboard = [
            [KeyboardButton("🇺🇦 Україна"), KeyboardButton("🇷🇺 Росія")],
            [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("🌍 Виберіть країну для пошуку:", reply_markup=reply_markup)
        return ENTERING_COUNTRY
    else:
        await update.message.reply_text("❌ Будь ласка, виберіть один з варіантів.")
        return ENTERING_SEARCH_TYPE

    keyboard = [
        [KeyboardButton("🌍 Змінити країну пошуку"), KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Натисніть 'Змінити країну', 'Назад' або 'Головне меню' для скасування запиту.", reply_markup=reply_markup)

    return ENTERING_SEARCH_DATA


conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("🌟 Почати пошук"), start_search)],
    states={
        ENTERING_COUNTRY: [MessageHandler(filters.TEXT, handle_country)],
        ENTERING_SEARCH_TYPE: [MessageHandler(filters.TEXT, handle_search_type)],
        ENTERING_SEARCH_DATA: [MessageHandler(filters.TEXT, handle_request_data)],
    },
    fallbacks=
        [MessageHandler(filters.TEXT & filters.Regex("^🔙 Назад$"), main_menu),
        MessageHandler(filters.TEXT & filters.Regex("^🏠 Головне меню$"), osint_shodan_menu)]
)