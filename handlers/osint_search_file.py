import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import CallbackContext, MessageHandler, filters, ConversationHandler
from api_clients import send_file_to_api, API_URL

logger = logging.getLogger(__name__)

SELECT_COUNTRY, WAITING_FOR_FILE = range(2)

async def main_menu(update: Update, context: CallbackContext):
    """Головне меню з кнопками для вибору."""
    keyboard = [
        [KeyboardButton("🌟 Почати пошук")],
        [KeyboardButton("📁 Шукати з файлу")],
        [KeyboardButton("🏠 Головне меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Оберіть дію:", reply_markup=reply_markup)


async def main_menu_N(update: Update, context: CallbackContext):
    """Головне меню з кнопками OSINT та Shodan."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Оберіть дію:", reply_markup=reply_markup)


async def return_to_main_menu(update: Update, context: CallbackContext):
    """Повернення до головного меню після натискання кнопки '◀️ Назад'."""
    await main_menu(update, context)
    return ConversationHandler.END


async def handle_file(update: Update, context: CallbackContext):
    """Отримання файлу та його надсилання в API."""
    tg_id = context.user_data.get("tg_id")
    api_key = context.user_data.get("api_key")
    country_code = context.user_data.get("country_code")

    if update.message.text == "🔙 Назад":
        await main_menu(update, context)
        return ConversationHandler.END

    if update.message.text == "🏠 Головне меню":
        await main_menu_N(update, context)
        return ConversationHandler.END

    if not tg_id or not api_key or not country_code:
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
        api_url = f"{API_URL}tg_request/generate_pdf/?tg_id={tg_id}&search_country={country_code}"
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
        [KeyboardButton("🇺🇦 Україна"), KeyboardButton("🇷🇺 Росія")],
        [KeyboardButton("🔙 Назад"), KeyboardButton("🏠 Головне меню")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text("🌍 Оберіть країну для нового пошуку або поверніться до меню:",
                                   reply_markup=reply_markup)

    return SELECT_COUNTRY


async def select_country(update: Update, context: CallbackContext):
    country = update.message.text.strip().lower()

    if country == "🔙 Назад":
        await main_menu(update, context)
        return ConversationHandler.END

    if country == "🏠 головне меню":
        await main_menu_N(update, context)
        return ConversationHandler.END

    country_mapping = {
        "🇺🇦 україна": "UA",
        "🇷🇺 росія": "RU"
    }

    if country in country_mapping:
        context.user_data["country_code"] = country_mapping[country]
        await update.message.reply_text(
            f"✅ Ви обрали пошук у країні '{country}'. Тепер надішліть Excel файл у форматі: \n"
            "id | ФИО | ИНН | НОМЕР ТЕЛЕФОНА | TG_ID | FACEBOOK_ID | VK_ID",
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
    else:
        await update.message.reply_text("❌ Будь ласка, виберіть коректну країну для пошуку.")
        return SELECT_COUNTRY


async def start_search_from_file(update: Update, context: CallbackContext):
    """Початок пошуку: вибір країни для пошуку."""
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
        "🌍 Виберіть країну для пошуку:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("🇺🇦 Україна"), KeyboardButton("🇷🇺 Росія")], ["🔙 Назад", "🏠 Головне меню"]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return SELECT_COUNTRY

conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("^📁 Шукати з файлу$"), start_search_from_file)],
    states={
        SELECT_COUNTRY: [
            MessageHandler(filters.TEXT & filters.Regex("^🔙 Назад$"), return_to_main_menu),
            MessageHandler(filters.TEXT & ~filters.COMMAND, select_country),
        ],
        WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL, handle_file)],
    },
    fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^🔙 Назад$"), return_to_main_menu)]
)
