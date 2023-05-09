from telegram import Update, Bot
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
)

from telegram.utils.request import Request

from config.settings import TELEGRAM_API_TOKEN

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


# Import all the command handlers
from bot.handlers.start_handler import StartHandler


### Telegram Bot ###

# Main function
def main() -> None:
    request = Request(connect_timeout=60, read_timeout=60)

    bot = Bot(token=TELEGRAM_API_TOKEN, request=request)

    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher


    # Add all the command handlers
    dp.add_handler(CommandHandler("start", StartHandler.start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()