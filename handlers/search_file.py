import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler
from api_clients import send_file_to_api, API_URL

logger = logging.getLogger(__name__)

SELECT_SEARCH_TYPE, WAITING_FOR_FILE = range(2)

async def main_menu(update: Update, context: CallbackContext):
    """Головне меню з кнопками для вибору."""
    keyboard = [
        [KeyboardButton("🌟 Почати пошук")],
        [KeyboardButton("📁 Шукати з файлу")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("👋 Привіт! Оберіть дію:", reply_markup=reply_markup)


async def return_to_main_menu(update: Update, context: CallbackContext):
    """Повернення до головного меню після натискання кнопки 'Головне меню'."""
    await main_menu(update, context)
    return ConversationHandler.END


async def handle_file(update: Update, context: CallbackContext):
    """Отримання файлу та його надсилання в API."""
    tg_id = context.user_data.get("tg_id")
    api_key = context.user_data.get("api_key")
    search_type = context.user_data.get("search_type")

    if update.message.text == "🏠 Головне меню":
        await main_menu(update, context)
        return ConversationHandler.END

    if not tg_id or not api_key or not search_type:
        await update.message.reply_text("❗ Сталася помилка. Спробуйте почати пошук знову.")
        return ConversationHandler.END

    document = update.message.document
    if not document:
        await update.message.reply_text("📁 Будь ласка, надішліть Excel файл.")
        return WAITING_FOR_FILE

    if not document.file_name.endswith((".xlsx", ".xls")):
        await update.message.reply_text("❌ Файл має бути у форматі Excel (.xlsx або .xls).")
        return WAITING_FOR_FILE

    try:
        file = await document.get_file()
        local_path = f"./{document.file_name}"
        await file.download_to_drive(local_path)
    except Exception as e:
        logger.error(f"Не вдалося завантажити файл: {e}")
        await update.message.reply_text("⚠️ Сталася помилка при завантаженні файлу. Спробуйте знову.")
        return WAITING_FOR_FILE

    command = {"📝 telegram id": "#", "📱 телефон": "PHONE", "👤 фіо": "FIO"}.get(search_type.lower())

    try:
        api_url = f"{API_URL}tg_request/generate_pdf/?tg_id={tg_id}&command={command}"
        response = await send_file_to_api(api_url, local_path, api_key)
    except Exception as e:
        logger.error(f"Помилка при виклику API: {e}")
        await update.message.reply_text("⚠️ Сталася помилка при обробці файлу.")
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    if response.get("error"):
        await update.message.reply_text(f"❌ Сталася помилка при обробці файлу: {response['error']}")
    else:
        await update.message.reply_text("✅ Файл успішно оброблено.")

    keyboard = [
        ["📝 Telegram ID", "📱 Телефон", "👤 ФІО"],
        [KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("🔍 Оберіть параметр для пошуку або натисніть кнопку для головного меню:",
                                    reply_markup=reply_markup)

    return SELECT_SEARCH_TYPE


async def select_search_type(update: Update, context: CallbackContext):
    """Обробка вибору параметра для пошуку."""
    search_type = update.message.text.strip().lower()

    if search_type == "🏠 головне меню":
        await main_menu(update, context)
        return ConversationHandler.END

    if search_type in ["📝 telegram id", "📱 телефон", "👤 фіо"]:
        context.user_data["search_type"] = search_type
        await update.message.reply_text(
            f"✅ Ви обрали пошук за '{search_type}'. Тепер надішліть Excel файл (Переконайтеся колонка з запитами має назву 'request_param').",
            reply_markup=ReplyKeyboardRemove(),
        )

        keyboard = [
            [KeyboardButton("🏠 Головне меню")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(
            "🔍 Оберіть параметр для пошуку або натисніть кнопку для головного меню:",
            reply_markup=reply_markup
        )
        return WAITING_FOR_FILE
    else:
        await update.message.reply_text("❌ Будь ласка, виберіть коректний параметр для пошуку.")
        return SELECT_SEARCH_TYPE


async def start_search_from_file(update: Update, context: CallbackContext):
    """Початок пошуку: вибір параметра для пошуку."""
    tg_id = str(update.message.from_user.id)
    context.user_data["tg_id"] = tg_id

    api_key = context.user_data.get("api_key")
    if not api_key:
        keyboard = [
            [KeyboardButton("🔑 Авторизуватися")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("❗ Ви не авторизовані. Щоб продовжити, натисніть кнопку для авторизації.",
                                        reply_markup=reply_markup)
        return ConversationHandler.END

    await update.message.reply_text(
        "🔍 Виберіть параметр для пошуку:",
        reply_markup=ReplyKeyboardMarkup(
            [["📝 Telegram ID", "📱 Телефон", "👤 ФІО"], ["🏠 Головне меню"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return SELECT_SEARCH_TYPE


conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^📁 Шукати з файлу$"), start_search_from_file)],
    states={
        SELECT_SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_search_type)],
        WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL, handle_file)],
    },
    fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^🏠 Головне меню$"), return_to_main_menu)],
)
