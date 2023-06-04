from telegram import Bot
from telegram.ext import Updater
from telegram.utils.request import Request
from config.settings import TELEGRAM_API_TOKEN
import pika
import os
import json
from telegram.ext import MessageHandler, Filters

def create_bot():
    request = Request(connect_timeout=60, read_timeout=60, con_pool_size=8)
    bot = Bot(token=TELEGRAM_API_TOKEN, request=request)
    return bot

def create_updater(bot):
    updater = Updater(bot=bot, use_context=True)
    return updater

def handle_update(update, context):
    url = os.environ['CLOUDAMQP_URL']
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='telegram_updates')
    channel.basic_publish(exchange='', routing_key='telegram_updates', body=json.dumps(update.to_dict()))
    connection.close()

bot = create_bot()
updater = create_updater(bot)


