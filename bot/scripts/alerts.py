import ccxt
from decimal import Decimal

from telegram.ext import CallbackContext
from telegram.error import BadRequest

# setup database
from bot.database import PriceAlertRequest, Session, PatternData, User

# setup logging
import logging

logger = logging.getLogger(__name__)


class PriceAlerts:
    @staticmethod
    def check_price_alerts(bot):
        session = Session()
        price_alert_requests = session.query(PriceAlertRequest).all()

        to_delete = []
        for price_alert_request in price_alert_requests:
            exchange = ccxt.coinbasepro()
            ticker = exchange.fetch_ticker(price_alert_request.symbol)
            current_price = ticker["last"]

            # If the current price is within 0.5% of the price alert request, send a message to the user
            if current_price >= price_alert_request.price_level * Decimal(
                "0.995"
            ) and current_price <= price_alert_request.price_level * Decimal("1.005"):
                bot.send_message(
                    chat_id=price_alert_request.user_id,
                    text=f"🔔 Price Alert! 🔔\n\nThe price of {price_alert_request.symbol} has reached your set level of {price_alert_request.price_level}. The current price is now: {current_price}.",
                )

                # Add the price alert request to the list of requests to be deleted
                to_delete.append(price_alert_request)

        # Delete all the price alert requests in the list
        for alert in to_delete:
            session.delete(alert)
        session.commit()



class PatternAlerts:
    def check_pattern_alerts(context: CallbackContext):
        session = Session()
        pattern_data_records = session.query(PatternData).all()
        users = session.query(User).filter_by(has_access=True).all()

        for user in users:
            alerts = []
            for pattern_data in pattern_data_records:
                alert = f"🔔 Pattern Alert! 🔔\n\n{pattern_data.pattern} has been detected on {pattern_data.symbol} / {pattern_data.timeframe} time frame."
                alerts.append(alert)

            if alerts:
                try:
                    context.bot.send_message(
                        chat_id=user.telegram_id, text="\n".join(alerts)
                    )
                except BadRequest as e:
                    logger.error(
                        f"Failed to send message to user {user.telegram_id}: {e.message}"
                    )
