import logging
import re
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, ConversationHandler
from api_clients import register_user
from handlers.search_file import start_search_from_file
from handlers.search_service import start_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PHONE_NUMBER = 1
OFFER_SEARCH = 2


async def start(update: Update, context: CallbackContext):
    """Стартова точка: отримання номера телефону."""
    logger.info("Користувач %s розпочав розмову.", update.effective_user.id)

    keyboard = [[KeyboardButton("🔑 Авторизуватися", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "👋 Привіт! Для реєстрації натисни кнопку '🔑 Авторизуватися'.",
        reply_markup=reply_markup,
    )
    return PHONE_NUMBER


def normalize_phone_number(phone_number: str) -> str:
    """Нормалізація номера телефону."""
    phone_number = re.sub(r"[^\d+]", "", phone_number)
    if phone_number.startswith("+"):
        phone_number = phone_number[1:]
    if phone_number.startswith("8"):
        phone_number = "380" + phone_number[1:]
    if phone_number.startswith("380") and len(phone_number) == 12:
        return phone_number
    return None


async def register(update: Update, context: CallbackContext):
    """Реєстрація користувача за номером телефону."""
    try:
        if update.message.contact:
            phone_number = update.message.contact.phone_number
        else:
            await update.message.reply_text("❌ Неможливо отримати номер телефону. Спробуйте ще раз.")
            return PHONE_NUMBER

        normalized_phone_number = normalize_phone_number(phone_number)
        if not normalized_phone_number:
            await update.message.reply_text("⚠️ Номер телефону має бути у форматі +380XXXXXXXXX. Спробуйте ще раз.")
            return PHONE_NUMBER

        logger.info("Користувач %s реєструє номер: %s", update.effective_user.id, normalized_phone_number)

        try:
            response = await register_user(normalized_phone_number)
            context.user_data["api_key"] = response.get("api_key")
            await update.message.reply_text("✅ Ваш номер телефону успішно зареєстровано.")
            await offer_search(update)
            return ConversationHandler.END

        except ValueError as ve:
            if "already exists" in str(ve):
                await update.message.reply_text("⚠️ Користувач з таким номером вже зареєстрований.")
                await offer_search(update)
                return ConversationHandler.END
            else:
                await update.message.reply_text(f"❌ Сталася помилка: {ve}")
        except Exception as e:
            await update.message.reply_text("❗ Помилка сервера. Спробуйте пізніше.")
            logger.exception("Помилка API: %s", e)

    except Exception as e:
        await update.message.reply_text("❗ Сталася непередбачена помилка. Спробуйте пізніше.")
        logger.exception("Помилка реєстрації: %s", e)

    return PHONE_NUMBER


async def offer_search(update: Update):
    """Пропозиція вибору пошуку."""
    keyboard = [
        [KeyboardButton("🌟 Почати пошук")],
        [KeyboardButton("📁 Шукати з файлу")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "🔎 Оберіть тип пошуку, натиснувши відповідну кнопку:",
        reply_markup=reply_markup,
    )
    return OFFER_SEARCH


conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE_NUMBER: [MessageHandler(filters.CONTACT, register)],
        OFFER_SEARCH: [
            MessageHandler(filters.Regex("^🌟 Почати пошук$"), start_search),
            MessageHandler(filters.Regex("^📁 Шукати з файлу$"), start_search_from_file),
        ],
    },
    fallbacks=[],
)
