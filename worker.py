import os
import pika
import time
import json
from telegram import Update
from telegram.ext import CallbackContext, Dispatcher, CommandHandler
from bot.bot_instance import bot
from bot.rate_limiting import TokenBucket

from config.settings import CLOUDAMQP_URL

# Import all the command handlers
from bot.command_handlers.start import StartHandler
from bot.command_handlers.subscribe import SubscribeHandler
from bot.command_handlers.help import HelpHandler
from bot.command_handlers.free.use_token import UseTokenHandler
from bot.command_handlers.free.join_waitlist import JoinWaitlistHandler
from bot.command_handlers.free.contact import ContactHandler
from bot.command_handlers.free.cotd import CotdHandler
from bot.command_handlers.free.global_top import GlobalTopHandler
from bot.command_handlers.free.whatsup import WhatsupHandler
from bot.command_handlers.free.gainers import GainersHandler
from bot.command_handlers.free.losers import LosersHandler
from bot.command_handlers.free.news import NewsHandler
from bot.command_handlers.free.request_alert import PriceAlertHandler
from bot.command_handlers.premium.wdom import WdomHandler
from bot.command_handlers.premium.sentiment import SentimentHandler
from bot.command_handlers.premium.positions import PositionsHandler
from bot.command_handlers.premium.plot_chart import ChartHandler
from bot.command_handlers.premium.stats import StatsHandler
from bot.command_handlers.premium.signal import SignalHandler

def main():
    url = CLOUDAMQP_URL
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='telegram_updates')

    # Initialize the token bucket with a rate of 30 messages per second and a capacity of 30 messages
    token_bucket = TokenBucket(30, 30)

    dispatcher = Dispatcher(bot, None, workers=0)
    dispatcher.add_handler(CommandHandler("start", StartHandler.start))
    dispatcher.add_handler(CommandHandler("help", HelpHandler.help))
    dispatcher.add_handler(CommandHandler("use_token", UseTokenHandler.use_token))
    dispatcher.add_handler(CommandHandler("join_waitlist", JoinWaitlistHandler.join_waitlist))
    dispatcher.add_handler(CommandHandler("cotd", CotdHandler.coin_of_the_day))
    dispatcher.add_handler(CommandHandler("global_top", GlobalTopHandler.global_top))
    dispatcher.add_handler(CommandHandler("whatsup", WhatsupHandler.whatsup))
    dispatcher.add_handler(CommandHandler("gainers", GainersHandler.gainers))
    dispatcher.add_handler(CommandHandler("losers", LosersHandler.losers))
    dispatcher.add_handler(CommandHandler("news", NewsHandler.news_handler))
    dispatcher.add_handler(CommandHandler("set_alert", PriceAlertHandler.request_price_alert))
    dispatcher.add_handler(CommandHandler("wdom", WdomHandler.wdom_handler))
    dispatcher.add_handler(CommandHandler("sentiment", SentimentHandler.sentiment))
    dispatcher.add_handler(CommandHandler("positions", PositionsHandler.trader_positions))
    dispatcher.add_handler(CommandHandler("chart", ChartHandler.plot_chart))
    dispatcher.add_handler(StatsHandler.command_handler())
    dispatcher.add_handler(SignalHandler.command_handler())



    def callback(ch, method, properties, body):
        update = json.loads(body)
        update = Update.de_json(update, bot)

        # Refill the token bucket
        token_bucket.refill()

        # Check if a token is available
        if token_bucket.consume():
            # If a token is available, process the update and acknowledge the message
            dispatcher.process_update(update)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        else:
            # If no token is available, do not acknowledge the message. so it will be requed
            print("Rate limit exceeded")
            pass

    channel.basic_consume(queue='telegram_updates', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main()

