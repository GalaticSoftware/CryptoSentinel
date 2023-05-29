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

from config.settings import TELEGRAM_API_TOKEN

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

from bot.scripts.price_alerts import PriceAlerts

# Free handlers
from bot.handlers.free.cotd import CotdHandler
from bot.handlers.free.global_top import GlobalTopHandler
from bot.handlers.free.whatsup import WhatsupHandler
from bot.handlers.free.gainers import GainersHandler
from bot.handlers.free.losers import LosersHandler
from bot.handlers.free.news import NewsHandler
from bot.handlers.free.request_alert import PriceAlertHandler

# Premium handlers
from bot.handlers.premium.wdom import WdomHandler
from bot.handlers.premium.sentiment import SentimentHandler
from bot.handlers.premium.positions import PositionsHandler
from bot.handlers.premium.plot_chart import ChartHandler
from bot.handlers.premium.info import InfoHandler

from users.management import check_expired_subscriptions

### Telegram Bot ###


def check_and_revoke_expired_subscriptions(context: CallbackContext):
    revoked_users = check_expired_subscriptions()
    if revoked_users is None:
        revoked_users = []

    for user_id in revoked_users:
        context.bot.send_message(user_id, "Your subscription has expired. Please subscribe again to regain access.")
        logger.info(f"Revoked access for user {user_id}")


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


    # Add all the free handlers to the dispatcher
    dp.add_handler(CommandHandler("start", StartHandler.start))
    dp.add_handler(CommandHandler("help", HelpHandler.help))
    dp.add_handler(CommandHandler("cotd", CotdHandler.coin_of_the_day))
    dp.add_handler(CommandHandler("global_top", GlobalTopHandler.global_top, pass_args=True))
    dp.add_handler(CommandHandler("use_token", UseTokenHandler.use_token))
    dp.add_handler(CommandHandler("gainers", GainersHandler.gainers))
    dp.add_handler(CommandHandler("losers", LosersHandler.losers))
    dp.add_handler(CommandHandler("news", NewsHandler.news_handler))
    dp.add_handler(CommandHandler("set_alert",
                                  PriceAlertHandler.request_price_alert,
                                  pass_args=True) )
    dp.add_handler(CommandHandler('list_alerts', PriceAlertHandler.list_alerts))
    dp.add_handler(CommandHandler('remove_alert', PriceAlertHandler.remove_alert, pass_args=True))


    # Add all the paid handlers to the dispatcher
    dp.add_handler(CommandHandler("whatsup", WhatsupHandler.whatsup))
    dp.add_handler(CommandHandler("wdom", WdomHandler.wdom_handler))
    dp.add_handler(CommandHandler("sentiment", SentimentHandler.sentiment))
    dp.add_handler(CommandHandler("positions", PositionsHandler.trader_positions))
    dp.add_handler(CommandHandler("chart", ChartHandler.plot_chart, pass_args=True))
    dp.add_handler(CommandHandler("info", InfoHandler.get_coin_info_command, pass_args=True))

    # Subscribe Handlers
    subscribe_handler = SubscribeHandler.subscribe_handler
    payment_handler = SubscribeHandler.payment_handler

    monthly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_monthly,
        pattern="^subscribe_monthly_subscription$"
        )
    
    three_monthly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_3_monthly,
        pattern="^subscribe_3_monthly_subscription$"
        )
    
    yearly_handler = CallbackQueryHandler(
        SubscribeHandler.send_invoice_yearly,
        pattern="^subscribe_yearly_subscription$"
        )


    dp.add_handler(subscribe_handler)
    dp.add_handler(payment_handler)
    dp.add_handler(monthly_handler)
    dp.add_handler(three_monthly_handler)
    dp.add_handler(yearly_handler)


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
