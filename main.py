from telegram import Update, Bot
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    Filters,
)

from telegram.utils.request import Request
from config.settings import TELEGRAM_API_TOKEN, X_RAPIDAPI_KEY

import threading
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Import all the command handlers
# Start and help handlers
from bot.handlers.start import StartHandler
from bot.handlers.subscribe import SubscribeHandler
from bot.handlers.help import HelpHandler
from bot.handlers.free.use_token import UseTokenHandler
from bot.handlers.free.join_waitlist import JoinWaitlistHandler
from bot.handlers.free.contact import ContactHandler

from bot.scripts.alerts import PriceAlerts  # PatternAlerts

# from CryptoSentinel.bot.scripts.fetcher import fetch_pattern_data

# Free handlers
from bot.handlers.free.cotd import CotdHandler
from bot.handlers.free.global_top import GlobalTopHandler
from bot.handlers.free.whatsup import WhatsupHandler
from bot.handlers.free.gainers import GainersHandler
from bot.handlers.free.losers import LosersHandler
from bot.handlers.free.news import NewsHandler
from bot.handlers.free.request_alert import PriceAlertHandler

# Premium handlersd
from bot.handlers.premium.wdom import WdomHandler
from bot.handlers.premium.sentiment import SentimentHandler
from bot.handlers.premium.positions import PositionsHandler
from bot.handlers.premium.plot_chart import ChartHandler
from bot.handlers.premium.stats import StatsHandler
from bot.handlers.premium.signal import SignalHandler

from users.management import check_expired_subscriptions
from bot.alerts.position_alerts import run_position_alerts
from data_analyzer_module.positions.fetcher import UIDFetcher
from data_analyzer_module.positions.scanner import (
    PositionsScanner,
    define_fetched_position,
    setup_database,
)
from data_analyzer_module.market.fetcher import OHLCVFetcher
from data_analyzer_module.market.alerts import IndicatorAlerts

### Telegram Bot ###


def check_and_revoke_expired_subscriptions(context: CallbackContext):
    revoked_users = check_expired_subscriptions()
    if revoked_users is None:
        revoked_users = []

    for user_id in revoked_users:
        context.bot.send_message(
            user_id,
            "Your subscription has expired. Please subscribe again to regain access.",
        )
        logger.info(f"Revoked access for user {user_id}")


# API setup
API_URL = "https://binance-futures-leaderboard1.p.rapidapi.com/v2/getTraderPositions"
HEADERS = {
    "X-RapidAPI-Key": X_RAPIDAPI_KEY,
    "X-RapidAPI-Host": "binance-futures-leaderboard1.p.rapidapi.com",
}


# Main function
def main() -> None:
    request = Request(connect_timeout=60, read_timeout=60)

    bot = Bot(token=TELEGRAM_API_TOKEN, request=request)

    updater = Updater(TELEGRAM_API_TOKEN, use_context=True)

    dp = updater.dispatcher
    jq = updater.job_queue

    # Schedule the job to check for expired subscriptions every 5 minutes (300 seconds)
    jq.run_repeating(check_and_revoke_expired_subscriptions, interval=300, first=0)
    # Schedule the job to check for price alerts every 30 seconds
    jq.run_repeating(PriceAlerts.check_price_alerts, interval=30, first=0)
    # # Run Fetcher every 4 hours
    # jq.run_repeating(fetch_pattern_data, interval=60, first=0)
    # # Run Pattern Alerts every 4 hours
    # jq.run_repeating(PatternAlerts.check_pattern_alerts, interval=60, first=0)

    # Run Positions Fetcher every 2 hours and the first time after 0 seconds
    fetcher = UIDFetcher(API_URL, HEADERS)
    jq.run_repeating(fetcher.run, interval=7200, first=0)

    # Create an instance of PositionsScanner
    logger = logging.getLogger(__name__)
    Session, Base = setup_database()
    FetchedPosition = define_fetched_position(Base)
    scanner = PositionsScanner(logger, Session, FetchedPosition)

    # Start a new thread to run the PositionsScanner
    scanner_thread = threading.Thread(target=scanner.run)
    scanner_thread.start()

    # Add all the free handlers to the dispatcher
    dp.add_handler(CommandHandler("start", StartHandler.start))
    dp.add_handler(CommandHandler("help", HelpHandler.help))
    dp.add_handler(CommandHandler("cotd", CotdHandler.coin_of_the_day))
    dp.add_handler(
        CommandHandler("global_top", GlobalTopHandler.global_top, pass_args=True)
    )
    dp.add_handler(CommandHandler("use_token", UseTokenHandler.use_token))
    dp.add_handler(CommandHandler("gainers", GainersHandler.gainers))
    dp.add_handler(CommandHandler("losers", LosersHandler.losers))
    dp.add_handler(CommandHandler("news", NewsHandler.news_handler))
    dp.add_handler(
        CommandHandler(
            "set_alert", PriceAlertHandler.request_price_alert, pass_args=True
        )
    )
    dp.add_handler(CommandHandler("list_alerts", PriceAlertHandler.list_alerts))
    dp.add_handler(
        CommandHandler("remove_alert", PriceAlertHandler.remove_alert, pass_args=True)
    )

    # Add all the paid handlers to the dispatcher
    dp.add_handler(CommandHandler("whatsup", WhatsupHandler.whatsup))
    # dp.add_handler(CommandHandler("wdom", WdomHandler.wdom_handler))
    dp.add_handler(CommandHandler("sentiment", SentimentHandler.sentiment))
    dp.add_handler(CommandHandler("positions", PositionsHandler.trader_positions))
    dp.add_handler(CommandHandler("chart", ChartHandler.plot_chart, pass_args=True))
    dp.add_handler(StatsHandler.command_handler())
    dp.add_handler(SignalHandler.command_handler())

    # Subscribe Handlers
    subscribe_handler = SubscribeHandler.subscribe_handler
    payment_handler = SubscribeHandler.payment_handler

    monthly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_monthly,
        pattern="^subscribe_monthly_subscription$",
    )

    three_monthly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_3_monthly,
        pattern="^subscribe_3_monthly_subscription$",
    )

    yearly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_yearly, pattern="^subscribe_yearly_subscription$"
    )

    # waitlist_handler = JoinWaitlistHandler.join_waitlist_handler
    dp.add_handler(CommandHandler("join_waitlist", JoinWaitlistHandler.join_waitlist))
    dp.add_handler(ContactHandler.conversation_handler())

    dp.add_handler(subscribe_handler)
    dp.add_handler(payment_handler)
    dp.add_handler(monthly_handler)
    dp.add_handler(three_monthly_handler)
    dp.add_handler(yearly_handler)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
