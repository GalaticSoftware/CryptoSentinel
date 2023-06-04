import requests
from decimal import Decimal
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from config.settings import X_RAPIDAPI_KEY, MY_POSTGRESQL_URL
from bot.utils import log_command_usage
import logging
import ccxt

logger = logging.getLogger(__name__)

# setup database
from database.models import PriceAlertRequest, Session

class PriceAlertHandler:
    @staticmethod
    def request_price_alert(update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        try:
            symbol, price_level = context.args
            price_level = Decimal(price_level)
            if price_level <= 0:
                update.message.reply_text("Invalid price level. Please enter a positive number.")
                return

            # Try to fetch the current price for the symbol
            exchange = ccxt.bybit()
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker['last']
        except (ValueError, IndexError):
            update.message.reply_text("Invalid input. Please enter a symbol and a price level.")
            return
        except ccxt.BaseError as e:
            logger.error(f"Failed to fetch the current price for {symbol}: {e}")
            update.message.reply_text(f"Invalid symbol. {symbol} is not listed on the exchange or not currently tradable.")
            return

        session = Session()
        price_alert_requests = PriceAlertRequest(user_id=user_id, symbol=symbol, price_level=price_level)
        session.add(price_alert_requests)
        session.commit()

        update.message.reply_text(f"Your request for a price alert has been successfully set up! You will receive a notification when the price of {symbol} reaches {price_level}.")

    @staticmethod
    def list_alerts(update: Update, context: CallbackContext):
        user_id = update.message.from_user.id

        session = Session()
        price_alert_requests = session.query(PriceAlertRequest).filter_by(user_id=user_id).all()

        if not price_alert_requests:
            update.message.reply_text("You have no price alerts set up.")
        else:
            message = "Here are your current price alerts:\n\n"
            for alert in price_alert_requests:
                message += f"ID: {alert.id}, Symbol: {alert.symbol}, Price Level: {alert.price_level}\n"
            update.message.reply_text(message)

    @staticmethod
    def remove_alert(update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        alert_id = int(context.args[0])

        session = Session()
        price_alert_request = session.query(PriceAlertRequest).filter_by(user_id=user_id, id=alert_id).first()

        if not price_alert_request:
            update.message.reply_text(f"No price alert found with ID {alert_id}.")
        else:
            session.delete(price_alert_request)
            session.commit()
            update.message.reply_text(f"Successfully removed price alert with ID {alert_id}.")
