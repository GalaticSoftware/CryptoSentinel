from bot.bot_instance import updater 
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
import pika
import json

# Import all the command handlers
# Start and help handlers
from bot.command_handlers.start import StartHandler
from bot.command_handlers.subscribe import SubscribeHandler
from bot.command_handlers.help import HelpHandler
from bot.command_handlers.free.use_token import UseTokenHandler
from bot.command_handlers.free.join_waitlist import JoinWaitlistHandler
from bot.command_handlers.free.contact import ContactHandler

from bot.scripts.alerts import PriceAlerts  # PatternAlerts

# from CryptoSentinel.bot.scripts.fetcher import fetch_pattern_data

# Free handlers
from bot.command_handlers.free.cotd import CotdHandler
from bot.command_handlers.free.global_top import GlobalTopHandler
from bot.command_handlers.free.whatsup import WhatsupHandler
from bot.command_handlers.free.gainers import GainersHandler
from bot.command_handlers.free.losers import LosersHandler
from bot.command_handlers.free.news import NewsHandler
from bot.command_handlers.free.request_alert import PriceAlertHandler

# Premium handlers
from bot.command_handlers.premium.wdom import WdomHandler
from bot.command_handlers.premium.sentiment import SentimentHandler
from bot.command_handlers.premium.positions import PositionsHandler
from bot.command_handlers.premium.plot_chart import ChartHandler
from bot.command_handlers.premium.stats import StatsHandler
from bot.command_handlers.premium.signal import SignalHandler

from config.settings import CLOUDAMQP_URL

### Telegram Bot ###

def main() -> None:

    dp = updater.dispatcher

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


    def process_update(update: Update, context: CallbackContext):
        url = CLOUDAMQP_URL
        params = pika.URLParameters(url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue='telegram_updates')
        channel.basic_publish(exchange='', routing_key='telegram_updates', body=json.dumps(update.to_dict()))
        connection.close()


    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    from bot.bot_instance import bot, updater
    main()
