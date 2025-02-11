from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackContext

from handlers.osint_handler import osint_search
from handlers.registration import register
from decouple import config
from handlers.search_service import conversation_handler as start_search_handler, start_search
from handlers.shd_req import start_search_sh, ENTERING_SEARCH_TYPE_SH, ENTERING_SEARCH_DATA_SH
from handlers.shodan_handler import shodan_search
from handlers.start_handler import start
from handlers.shd_req import conversation_handler as shd_handler_s
from handlers.osint_search_file import conversation_handler as os_h_f, main_menu_N
from handlers.shd_file import conversation_handler as shd_f
TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")

PHONE_NUMBER = 1
CHOOSE_SEARCH_TYPE = 2
async def osint_shodan_menu(update: Update, context: CallbackContext):
    """Меню з кнопками OSINT та Shodan."""
    keyboard = [
        [KeyboardButton("🕵️‍♂️ OSINT")],
        [KeyboardButton("🌐 Shodan")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("🔍 Оберіть інструмент:", reply_markup=reply_markup)



conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE_NUMBER: [MessageHandler(filters.CONTACT, register)],
        CHOOSE_SEARCH_TYPE: [
            MessageHandler(filters.Regex("^🕵️‍♂️ OSINT$"), osint_search),
            MessageHandler(filters.Regex("^🌐 Shodan$"), shodan_search),
        ],
    },
    fallbacks=[],
)
def main():

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(conversation_handler)
    application.add_handler(start_search_handler)
    application.add_handler(shd_handler_s)
    application.add_handler(os_h_f)
    application.add_handler(shd_f)
    application.add_handler(MessageHandler(filters.Regex("^🕵️‍♂️ OSINT$"), osint_search))
    application.add_handler(MessageHandler(filters.Regex("^🌐 Shodan$"), shodan_search))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🏠 Головне меню$"), osint_shodan_menu))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^🔑 Авторизуватися$"), osint_shodan_menu))


    application.run_polling()


if __name__ == "__main__":
    main()