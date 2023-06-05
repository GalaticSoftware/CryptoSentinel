from bot.bot_instance import updater 
from telegram.ext import MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram import Update
import pika
import json
from config.settings import CLOUDAMQP_URL
from bot.command_handlers.accept_privacy_policy import accept_privacy_policy
from bot.command_handlers.subscribe import SubscribeHandler

# Create a persistent RabbitMQ connection and channel
url = CLOUDAMQP_URL
params = pika.URLParameters(url)
connection = pika.BlockingConnection(params)
channel = connection.channel()
channel.queue_declare(queue='telegram_updates')

def process_update(update: Update, context: CallbackContext):
    try:
        # Publish the update to the RabbitMQ queue
        channel.basic_publish(
            exchange='',
            routing_key='telegram_updates',
            body=json.dumps(update.to_dict()),
            properties=pika.BasicProperties(delivery_mode=2),  # Make message persistent
        )
    except Exception as e:
        print(f"Error publishing message to RabbitMQ: {e}")

def main() -> None:
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.all, process_update))
    dp.add_handler(CallbackQueryHandler(accept_privacy_policy, pattern="^accept_privacy_policy$"))

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

    dp.add_handler(subscribe_handler)
    dp.add_handler(payment_handler)
    dp.add_handler(monthly_handler)
    dp.add_handler(three_monthly_handler)
    dp.add_handler(yearly_handler)

    updater.start_polling()
    updater.idle()

    # Close the RabbitMQ connection when the application is shutting down
    connection.close()

if __name__ == "__main__":
    from bot.bot_instance import bot, updater
    main()

