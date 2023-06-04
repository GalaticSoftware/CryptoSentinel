from bot.bot_instance import updater 
from telegram.ext import MessageHandler, Filters, CallbackContext
from telegram import Update
import pika
import json
from config.settings import CLOUDAMQP_URL

def main() -> None:

    dp = updater.dispatcher

    def process_update(update: Update, context: CallbackContext):
        url = CLOUDAMQP_URL
        params = pika.URLParameters(url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue='telegram_updates')
        channel.basic_publish(exchange='', routing_key='telegram_updates', body=json.dumps(update.to_dict()))
        connection.close()

    dp.add_handler(MessageHandler(Filters.all, process_update))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    from bot.bot_instance import bot, updater
    main()

