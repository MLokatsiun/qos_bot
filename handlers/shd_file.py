import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler
from api_clients import send_file_to_api, API_URL, send_file_to_api_shd

logger = logging.getLogger(__name__)

WAITING_FOR_FILE = 1

async def main_menu_N(update: Update, context: CallbackContext):
    """Головне меню з кнопками для вибору."""
    keyboard = [
        [KeyboardButton("🌐 Пошук в мережі")],
        [KeyboardButton("📁 Шукати з файлу Shodan")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("👋 Привіт! Оберіть дію:", reply_markup=reply_markup)
    return ConversationHandler.END  # Повертаємо стан, щоб ConversationHandler залишався активним

async def return_to_main_menu_n(update: Update, context: CallbackContext):
    await main_menu_N(update, context)
    return ConversationHandler.END

async def main_menu(update: Update, context: CallbackContext):
    """Головне меню з кнопками для вибору."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("👋 Привіт! Оберіть дію:", reply_markup=reply_markup)
    return ConversationHandler.END

async def return_to_main_menu(update: Update, context: CallbackContext):
    """Повернення до головного меню після натискання кнопки 'Головне меню'."""
    await main_menu(update, context)
    return ConversationHandler.END


async def handle_file(update: Update, context: CallbackContext):
    """Отримання файлу та його надсилання в API."""
    tg_id = context.user_data.get("tg_id")
    api_key = context.user_data.get("api_key")

    if update.message.text == "🏠 Головне меню":
        await return_to_main_menu(update, context)
        return ConversationHandler.END

    if not tg_id or not api_key:
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

    try:
        api_url = f"{API_URL}request/shd/?tg_id={tg_id}"
        response = await send_file_to_api_shd(api_url, local_path, api_key)
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
        [KeyboardButton("🌐 Пошук в мережі")],
        [KeyboardButton("📁 Шукати з файлу Shodan")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("🔍 Оберіть наступну дію:", reply_markup=reply_markup)

    return ConversationHandler.END


async def start_search_from_file_shd(update: Update, context: CallbackContext):
    """Початок пошуку: запит на надсилання файлу."""
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
        "📁 Будь ласка, надішліть Excel файл у форматі: \n"
        "id | IP | GEO",
        reply_markup=ReplyKeyboardRemove(),
    )

    keyboard = [
        [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🔍 Надішліть файл або поверніться до головного меню:",
        reply_markup=reply_markup
    )
    return WAITING_FOR_FILE


conversation_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.TEXT & filters.Regex("^📁 Шукати з файлу Shodan$"), start_search_from_file_shd),
    ],
    states={
        WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL, handle_file)],
    },
    fallbacks=[
        MessageHandler(filters.TEXT & filters.Regex("^🔙 Назад$"), return_to_main_menu_n),
        MessageHandler(filters.TEXT & filters.Regex("^🏠 Головне меню$"), return_to_main_menu),
    ]
)