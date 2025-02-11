from telegram import Update
from telegram.ext import CallbackContext
import logging
from api_clients import register_user
import re

from handlers.search_handler import choose_search_type

logger = logging.getLogger(__name__)

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
            return 1

        normalized_phone_number = normalize_phone_number(phone_number)
        if not normalized_phone_number:
            await update.message.reply_text("⚠️ Номер телефону має бути у форматі +380XXXXXXXXX. Спробуйте ще раз.")
            return 1

        logger.info("Користувач %s реєструє номер: %s", update.effective_user.id, normalized_phone_number)

        try:
            response = await register_user(normalized_phone_number)
            context.user_data["api_key"] = response.get("api_key")
            await update.message.reply_text("✅ Ваш номер телефону успішно зареєстровано.")
            await choose_search_type(update)
            return 2

        except ValueError as ve:
            if "already exists" in str(ve):
                await update.message.reply_text("⚠️ Користувач з таким номером вже зареєстрований.")
                await choose_search_type(update)
                return 2
            else:
                await update.message.reply_text(f"❌ Сталася помилка: {ve}")
        except Exception as e:
            await update.message.reply_text("❗ Помилка сервера. Спробуйте пізніше.")
            logger.exception("Помилка API: %s", e)

    except Exception as e:
        await update.message.reply_text("❗ Сталася непередбачена помилка. Спробуйте пізніше.")
        logger.exception("Помилка реєстрації: %s", e)

    return 1
