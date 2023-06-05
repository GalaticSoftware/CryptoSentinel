import pika
import json
from telegram import Update
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, CallbackContext
from bot.bot_instance import bot, updater
from bot.bot_instance import bot
from bot.rate_limiting import TokenBucket

from config.settings import CLOUDAMQP_URL

# Import all the command handlers
from bot.command_handlers.start import StartHandler
from bot.command_handlers.help import HelpHandler
from bot.command_handlers.free.use_token import UseTokenHandler, UseReferralCode
from bot.command_handlers.free.join_waitlist import JoinWaitlistHandler
from bot.command_handlers.free.contact import ContactHandler
from bot.command_handlers.free.cotd import CotdHandler
from bot.command_handlers.free.global_top import GlobalTopHandler
from bot.command_handlers.free.whatsup import WhatsupHandler
from bot.command_handlers.free.gainers import GainersHandler
from bot.command_handlers.free.losers import LosersHandler
from bot.command_handlers.free.news import NewsHandler
from bot.command_handlers.free.request_alert import PriceAlertHandler
from bot.command_handlers.premium.sentiment import SentimentHandler
from bot.command_handlers.premium.positions import PositionsHandler
from bot.command_handlers.premium.plot_chart import ChartHandler
from bot.command_handlers.premium.stats import StatsHandler
from bot.command_handlers.premium.signal import SignalHandler

from bot.scripts.alerts import PriceAlerts
from database.management import check_expired_subscriptions
from apscheduler.schedulers.background import BackgroundScheduler

# Import and setup logging
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

import time

def send_heartbeat(channel):
    while True:
        channel.basic_publish(exchange='', routing_key='heartbeat', body='heartbeat')
        time.sleep(30)

def main():
    url = CLOUDAMQP_URL
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='telegram_updates')
    channel.queue_declare(queue='heartbeat') # declare the queue for heartbeat

    # start a thread to send heartbeat
    import threading
    threading.Thread(target=send_heartbeat, args=(channel,)).start()

    # Initialize the token bucket with a rate of 20 messages per second and a capacity of 20 messages
    token_bucket = TokenBucket(20, 20)

    dp = Dispatcher(bot, None, workers=1)

    scheduler = BackgroundScheduler()
    scheduler.start()

    # Schedule the job to check for expired subscriptions every 5 minutes (300 seconds)
    scheduler.add_job(check_expired_subscriptions, 'interval', minutes=5, args=[dp])
    # Schedule the job to check for price alerts every 30 seconds
    scheduler.add_job(PriceAlerts.check_price_alerts, 'interval', seconds=30, args=[dp])

    # Add all the free handlers to the dispatcher
    dp.add_handler(CommandHandler("start", StartHandler.start))
    dp.add_handler(CommandHandler("help", HelpHandler.help))
    dp.add_handler(CommandHandler("cotd", CotdHandler.coin_of_the_day))
    dp.add_handler(
        CommandHandler("global_top", GlobalTopHandler.global_top, pass_args=True)
    )
    dp.add_handler(CommandHandler("use_token", UseTokenHandler.use_token))
    dp.add_handler(CommandHandler("use_ref_code", UseReferralCode.use_referral_code))
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

    # waitlist_handler = JoinWaitlistHandler.join_waitlist_handler
    dp.add_handler(CommandHandler("join_waitlist", JoinWaitlistHandler.join_waitlist))
    dp.add_handler(ContactHandler.conversation_handler())

    def callback(ch, method, properties, body):
        update = json.loads(body)
        update = Update.de_json(update, bot)

        # Refill the token bucket
        token_bucket.refill()

        # Check if a token is available
        if token_bucket.consume():
            # If a token is available, process the update and acknowledge the message
            try:
                dp.process_update(update)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing update: {e}")
        else:
            # If no token is available, do not acknowledge the message. so it will be requed
            print("Rate limit exceeded")

    channel.basic_consume(queue='telegram_updates', on_message_callback=callback, auto_ack=False)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == "__main__":
    logger.info("Starting bot")
    main()

