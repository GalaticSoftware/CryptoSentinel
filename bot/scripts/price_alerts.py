import ccxt
from decimal import Decimal

from telegram.ext import CallbackContext

# setup database
from bot.database import PriceAlertRequest, Session

# setup logging
import logging
logger = logging.getLogger(__name__)

class PriceAlerts:
    def check_price_alerts(context: CallbackContext):
        session = Session()
        price_alert_requests = session.query(PriceAlertRequest).all()

        to_delete = []
        for price_alert_request in price_alert_requests:
            exchange = ccxt.bybit()
            ticker = exchange.fetch_ticker(price_alert_request.symbol)
            current_price = ticker['last']

            # If the current price is within 0.5% of the price alert request, send a message to the user
            if current_price >= price_alert_request.price_level * Decimal('0.995') and current_price <= price_alert_request.price_level * Decimal('1.005'):
                context.bot.send_message(
                    chat_id=price_alert_request.user_id,
                    text=f"🔔 Price Alert! 🔔\n\nThe price of {price_alert_request.symbol} has reached your set level of {price_alert_request.price_level}. The current price is now: {current_price}."
                )

                # Add the price alert request to the list of requests to be deleted
                to_delete.append(price_alert_request)

        # Delete all the price alert requests in the list
        for alert in to_delete:
            session.delete(alert)
        session.commit()
