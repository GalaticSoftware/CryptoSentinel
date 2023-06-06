# This script listens for updates from the Telegram API.
# When it receives a message, it publishes the message to a RabbitMQ queue.

import pika
from pika.exceptions import AMQPConnectionError, ConnectionClosedByBroker
import json
import logging
import telegram
import ssl
from telegram import Update
from telegram.ext import (
    CallbackContext,
    MessageHandler,
    Updater,
    Filters,
)

from telegram.utils.request import Request
import signal
import sys

from config.settings import TELEGRAM_API_TOKEN, CLOUDAMQP_URL

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# setup connection to RabbitMQ
params = pika.URLParameters(CLOUDAMQP_URL)
# configure heartbeat to keep connection open (even when idle for a long time) to avoid timeouts
# send heartbeat every 30 seconds
params.heartbeat = 30
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='telegram')

# Handle messages
# When a message is received, publish it to RabbitMQ
# The message should include the update_id, chat_id, and message text
def handle_message(update: Update, context: CallbackContext) -> None:
    global connection
    global channel
    logging.info('Received message: %s', update.message.text)
    update_dict = update.to_dict()
    update_json = json.dumps(update_dict, default=str)  # handle None values
    while True:
        try:
            channel.basic_publish(exchange='',
                                  routing_key='telegram',
                                  body=update_json)
            logging.info('Update published to RabbitMQ')
            break
        except (ConnectionClosedByBroker, AMQPConnectionError, ssl.SSLEOFError) as err:
            logging.error('Could not publish update to RabbitMQ: %s', err)
            # Reconnect to RabbitMQ
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue='telegram')




# Signal handling for graceful shutdown
def signal_handler(sig, frame):
    logging.info('Signal received, closing RabbitMQ connection...')
    connection.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Main function
def main() -> None:
    request = Request(connect_timeout=60, read_timeout=60, con_pool_size=8)
    bot = telegram.Bot(token=TELEGRAM_API_TOKEN, request=request)
    updater = Updater(bot=bot, use_context=True)

    # Listen for messages
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    # Publish messages to RabbitMQ
    logging.info('Listening for messages...')
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

