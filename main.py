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
# Start and help handlers
from CryptoSentinel.bot.handlers.start import StartHandler
from CryptoSentinel.bot.handlers.subscribe import SubscribeHandler
from CryptoSentinel.bot.handlers.help import HelpHandler
from CryptoSentinel.bot.handlers.free.use_token import UseTokenHandler

# Free handlers
from CryptoSentinel.bot.handlers.free.cotd import CotdHandler
from CryptoSentinel.bot.handlers.free.global_top import GlobalTopHandler
from CryptoSentinel.bot.handlers.free.sentiment import SentimentHandler

# Premium handlers
from CryptoSentinel.bot.handlers.premium.whatsup import WhatsupHandler
from CryptoSentinel.bot.handlers.premium.wdom import WdomHandler
from CryptoSentinel.bot.handlers.premium.news import NewsHandler


### Telegram Bot ###

# Main function
def main() -> None:
    request = Request(connect_timeout=60, read_timeout=60)

    bot = Bot(token=TELEGRAM_API_TOKEN, request=request)

    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher


    # Add all the free handlers to the dispatcher
    dp.add_handler(CommandHandler("start", StartHandler.start))
    dp.add_handler(CommandHandler("help", HelpHandler.help))
    dp.add_handler(CommandHandler("cotd", CotdHandler.coin_of_the_day))
    dp.add_handler(CommandHandler("global_top", GlobalTopHandler.global_top, pass_args=True))
    dp.add_handler(CommandHandler("sentiment", SentimentHandler.sentiment))
    dp.add_handler(CommandHandler("use_token", UseTokenHandler.use_token))


    # Add all the paid handlers to the dispatcher
    dp.add_handler(CommandHandler("whatsup", WhatsupHandler.whatsup))
    dp.add_handler(CommandHandler("wdom", WdomHandler.wdom_handler))
    dp.add_handler(CommandHandler("news", NewsHandler.news_handler))

    # Subscribe Handlers
    subscribe_handler = CallbackQueryHandler(SubscribeHandler.subscribe, pattern="^subscribe$")
    dp.add_handler(subscribe_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()