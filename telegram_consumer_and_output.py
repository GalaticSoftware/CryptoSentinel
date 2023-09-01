import pika
import json
import logging
import telegram
import time
import threading
from importlib import import_module
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler
from config.settings import TELEGRAM_API_TOKEN, CLOUDAMQP_URL
from bot.handlers.subscribe import SubscribeHandler
from users.management import check_expired_subscriptions

# Initialize logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
QUEUE_NAME = 'telegram'
RATE_LIMIT = 30

# Initialize RabbitMQ
params = pika.URLParameters(CLOUDAMQP_URL)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue=QUEUE_NAME)

# Initialize Telegram Bot and Dispatcher
bot = telegram.Bot(token=TELEGRAM_API_TOKEN)
dp = Dispatcher(bot, None, workers=1)

# Dynamic Import of Handlers
handler_modules = [
    # ... add all your handlers here
    'start', 'subscribe', 'help', 'use_token', 'join_waitlist', 'contact',
]

for module in handler_modules:
    mod = import_module(f'bot.handlers.{module}')
    dp.add_handler(CommandHandler(module, getattr(
        mod, f"{module.capitalize()}Handler").start))

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
def main():
    logger.info('Listening for messages...')
    channel.basic_consume(
        queue='telegram', on_message_callback=process_message, auto_ack=False)
    channel.start_consuming()


if __name__ == '__main__':
    check_and_revoke_expired_subscriptions()
    main()
