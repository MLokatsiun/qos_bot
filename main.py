from telegram.ext import Application
from handlers.registration import conversation_handler as registration_handler
from decouple import config
from handlers.search_service import conversation_handler as start_search_handler
from handlers.search_file import conversation_handler as handler_files

# Стани
PHONE_NUMBER = 1

TELEGRAM_TOKEN = config("TELEGRAM_TOKEN")

def main():

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(registration_handler)
    application.add_handler(start_search_handler)
    application.add_handler(handler_files)

    application.run_polling()


if __name__ == "__main__":
    main()