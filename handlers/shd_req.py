import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler, CommandHandler
from api_clients import send_request_to_api_shd

logger = logging.getLogger(__name__)

ENTERING_SEARCH_TYPE_SH, ENTERING_SEARCH_DATA_SH = range(2)

async def start_search_sh(update: Update, context: CallbackContext):
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
        [KeyboardButton("🔍 Шукати за координатами"),
         KeyboardButton("📱 Шукати по IP")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Виберіть, як шукати:", reply_markup=reply_markup)
    return ENTERING_SEARCH_TYPE_SH

async def osint_shodan_menu(update: Update, context: CallbackContext):
    """Меню з кнопками OSINT та Shodan."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🔍 Оберіть інструмент:", reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_search_type_sh(update: Update, context: CallbackContext):
    """Обробка вибору типу пошуку."""
    search_type = update.message.text.strip()
    logger.info(f"Користувач обрав тип пошуку: {search_type}")

    if search_type == '🔍 Шукати за координатами':
        await update.message.reply_text("🔍 Будь ласка, введіть координати для пошуку в форматі '51.55740, 29.88185'.")
        context.user_data["search_type"] = "GEO"
    elif search_type == '📱 Шукати по IP':
        await update.message.reply_text("📱 Будь ласка, введіть IP для пошуку.")
        context.user_data["search_type"] = "PHONE"
    elif search_type == '🔙 Назад':
        return await main_menu_T(update, context)
    elif search_type == "🏠 Головне меню":
        await osint_shodan_menu(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Будь ласка, виберіть один з варіантів.")
        return ENTERING_SEARCH_TYPE_SH

    keyboard = [[KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Натисніть 'Головне меню' для скасування запиту.", reply_markup=reply_markup)

    logger.info("Перехід до стану ENTERING_SEARCH_DATA_SHD")
    return ENTERING_SEARCH_DATA_SH


async def handle_request_data_sh(update: Update, context: CallbackContext):
    """Обробка запиту за введеними даними."""
    logger.info(f"Отримано дані для пошуку: {update.message.text}")

    search_data = update.message.text.strip()
    search_type = context.user_data.get("search_type")
    tg_id = context.user_data.get("tg_id")
    api_key = context.user_data.get("api_key")

    if update.message.text == "🏠 Головне меню":
        await osint_shodan_menu(update, context)
        return ConversationHandler.END

    if not tg_id or not api_key:
        keyboard = [[KeyboardButton("🔑 Авторизуватися")]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "❗ Ви не зареєстровані або не маєте API ключа. Щоб продовжити, натисніть кнопку для авторизації.",
            reply_markup=reply_markup)
        return ConversationHandler.END

    logger.info(f"Відправка запиту до API: tg_id={tg_id}, search_data={search_data}, search_type={search_type}")

    response = await send_request_to_api_shd(tg_id, search_data, search_type, api_key)

    if response.get("error"):
        await update.message.reply_text(f"❌ Сталася помилка при пошуку: {response['error']}")
    else:
        request_ids = ", ".join(response.get("request_ids", []))
        await update.message.reply_text(f"✅ Запит успішно надіслано.\n\nRequest IDs: {request_ids}")

    keyboard = [
        [KeyboardButton("🔍 Шукати за координатами"),
         KeyboardButton("📱 Шукати по IP")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("Оберіть, що робити далі:", reply_markup=reply_markup)

    return ENTERING_SEARCH_TYPE_SH


async def main_menu_T(update: Update, context: CallbackContext):
    """Головне меню."""
    keyboard = [
        [KeyboardButton("🌐 Пошук в мережі")],
        [KeyboardButton("📁 Шукати з файлу Shodan")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("👋 Привіт! Ось що ти можеш зробити:", reply_markup=reply_markup)
    return ConversationHandler.END


conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("🌐 Пошук в мережі"), start_search_sh)],
    states={
        ENTERING_SEARCH_TYPE_SH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_type_sh)
        ],
        ENTERING_SEARCH_DATA_SH: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_request_data_sh)
        ],
    },
    fallbacks=[MessageHandler(filters.TEXT & filters.Regex("🔙 Назад"), main_menu_T),
               MessageHandler(filters.TEXT & filters.Regex("🏠 Головне меню"), osint_shodan_menu)],
)

