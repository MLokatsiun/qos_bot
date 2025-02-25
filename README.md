# Telegram Bot

This project is a Telegram bot that supports user registration and PDF search functionality. The bot is also integrated with OSINT and Shodan for advanced information search.

## Installation

### Requirements
- Python 3.8+
- Installed dependencies from `requirements.txt`
- Telegram bot token

### Installing Dependencies
```sh
pip install -r requirements.txt
```

## Configuration
Create a `.env` file in the root directory and specify the necessary environment variables:
```
TELEGRAM_TOKEN=your_telegram_bot_token
```

## Running the Bot

```sh
python main.py
```

## Features
### Main Commands:
- `/start` – Start the bot
- Register a user
- OSINT search
- Shodan search
- PDF file search

## Project Structure
```
project_root/
│-- handlers/                # Command and message handlers
│   │-- osint_handler.py     # OSINT search handler
│   │-- osint_search_file.py # File-based OSINT search
│   │-- registration.py      # User registration
│   │-- search_handler.py    # Main search handler
│   │-- search_service.py    # Search service
│   │-- shd_file.py          # File search handler
│   │-- shd_req.py           # Shodan request handler
│   │-- shodan_handler.py    # Shodan search handler
│   │-- start_handler.py     # Start command handler
│-- main.py                  # Main bot script
│-- requirements.txt         # List of dependencies
│-- .gitignore               # Ignored files
│-- Dockerfile               # Docker build file
```

## Contact
If you have any questions or suggestions, feel free to reach out.

---

This README can be further improved based on your requirements.

