# This script establishes a connection to RabbitMQ and listens for messages from the telegram que.
# Initialize the The Telegram Bot to process the messages as they come in.
# (messages are commands from users that will be processed by the bot)
# Rate Limiting:
# Telegram has a rate limit of 30 messages per second.
# use the TokenBucket algorithm to limit the rate of messages sent to Telegram.
# Message Processing:
# Define a function to process messages from the queue.
# This function should consume messages from the queue and process them via the dispatcher command handlers of the bot.
# # Main Function:
# start consuming messages from the RabbitMQ queue.
# You'll need to handle any potential errors that could occur during this process,
# and you should also ensure that the RabbitMQ connection is
# closed when the application shuts down.


import pika
import json
import logging
import telegram
import time
import threading
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    MessageHandler,
    Updater,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    Filters,
    Dispatcher,
)
from telegram.error import (
    TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

from config.settings import TELEGRAM_API_TOKEN, CLOUDAMQP_URL

# Import all the command handlers
# Start and help handlers
from bot.handlers.start import StartHandler
from bot.handlers.subscribe import SubscribeHandler
from bot.handlers.help import HelpHandler
from bot.handlers.free.use_token import UseTokenHandler
from bot.handlers.free.join_waitlist import JoinWaitlistHandler
from bot.handlers.free.contact import ContactHandler


# from CryptoSentinel.bot.scripts.fetcher import fetch_pattern_data

# Free handlers
from bot.handlers.free.cotd import CotdHandler
from bot.handlers.free.global_top import GlobalTopHandler
from bot.handlers.free.whatsup import WhatsupHandler
from bot.handlers.free.gainers import GainersHandler
from bot.handlers.free.losers import LosersHandler
from bot.handlers.free.news import NewsHandler
from bot.handlers.free.request_alert import PriceAlertHandler
from bot.handlers.referral import UseReferralHandler

# Premium handlers
from bot.handlers.premium.wdom import WdomHandler
from bot.handlers.premium.sentiment import SentimentHandler
from bot.handlers.premium.positions import PositionsHandler
from bot.handlers.premium.plot_chart import ChartHandler
from bot.handlers.premium.stats import StatsHandler
from bot.handlers.premium.signal import SignalHandler

from users.management import check_expired_subscriptions

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)

# setup connection to RabbitMQ
params = pika.URLParameters(CLOUDAMQP_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='telegram')

# Initialize the Telegram Bot
bot = telegram.Bot(token=TELEGRAM_API_TOKEN)

# Initialize the Dispatcher
dp = Dispatcher(bot, None, workers=1)


# Add all command handlers to the Dispatcher
# Add all the free handlers to the dispatcher
dp.add_handler(CommandHandler("start", StartHandler.start))
# dp.add_handler(CommandHandler("use_referral", UseReferralHandler.use_referral))
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
    CommandHandler(
        "remove_alert", PriceAlertHandler.remove_alert, pass_args=True)
)

# Add all the paid handlers to the dispatcher
dp.add_handler(CommandHandler("whatsup", WhatsupHandler.whatsup))
# dp.add_handler(CommandHandler("wdom", WdomHandler.wdom_handler))
dp.add_handler(CommandHandler("sentiment", SentimentHandler.sentiment))
dp.add_handler(CommandHandler("positions", PositionsHandler.trader_positions))
dp.add_handler(CommandHandler(
    "chart", ChartHandler.plot_chart, pass_args=True))
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
dp.add_handler(CommandHandler("join_waitlist",
               JoinWaitlistHandler.join_waitlist))
dp.add_handler(ContactHandler.conversation_handler())

dp.add_handler(subscribe_handler)
dp.add_handler(payment_handler)
dp.add_handler(monthly_handler)
dp.add_handler(three_monthly_handler)
dp.add_handler(yearly_handler)


# Rate Limiting
# Telegram has a rate limit of 30 messages per second.
def rate_limited(max_per_second):
    """
    Decorator that make functions not be called faster than
    """
    min_interval = 1.0 / float(max_per_second)

    def decorate(func):
        last_time_called = [0.0]

        def rate_limited_function(*args, **kargs):
            elapsed = time.perf_counter() - last_time_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kargs)
            last_time_called[0] = time.perf_counter()
            return ret
        return rate_limited_function
    return decorate


def check_and_revoke_expired_subscriptions():
    revoked_users = check_expired_subscriptions()
    if revoked_users is None:
        revoked_users = []

    for user_id in revoked_users:
        bot.send_message(
            user_id,
            "Your subscription has expired. Please subscribe again to regain access.",
        )
        logger.info(f"Revoked access for user {user_id}")

    # Schedule the next run of this function
    threading.Timer(300, check_and_revoke_expired_subscriptions).start()


# Message Processing
@rate_limited(30)
def process_message(ch, method, properties, body):
    # Deserialize update from queue
    update_json = body.decode('utf-8')
    update_dict = json.loads(update_json)
    # Process update
    try:
        logging.info('Processing update: %s', update_dict)
        dp.process_update(telegram.Update.de_json(update_dict, bot))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except (TelegramError, ValueError) as err:
        logging.error('Could not process update: %s', err)


# Main Function
def main() -> None:
    # Listen for messages
    logging.info('Listening for messages...')
    channel.basic_consume(
        queue='telegram', on_message_callback=process_message, auto_ack=False)
    channel.start_consuming()


if __name__ == '__main__':
    # add 2 recurring jobs
    # 1. check for expired subscriptions
    # 2. check for price alerts
    check_and_revoke_expired_subscriptions()
    main()
