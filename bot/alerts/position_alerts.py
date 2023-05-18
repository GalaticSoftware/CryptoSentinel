import os
import sys
import pytz
from sqlalchemy import create_engine, select, desc, func, and_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from telegram import Bot
from config.settings import TELEGRAM_API_TOKEN, MY_POSTGRESQL_URL
from bot.database import Position, User, Alert
from telegram.ext import CallbackContext

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a SQLAlchemy session
engine = create_engine(MY_POSTGRESQL_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Initialize the Telegram bot
bot = Bot(token=TELEGRAM_API_TOKEN)

from telegram.error import BadRequest

def format_position(position):
    """Format a position for display in an alert."""
    return f"Symbol: {position.symbol}\n" \
           f"Entry Price: {position.entry_price}\n" \
           f"Position Cost: {position.position_cost}\n" \
           f"Open Time: {position.open_time}\n" \
           f"Close Time: {position.close_time}\n" \
           f"Profit/Loss: {position.pnl}\n"

def send_alert_to_users(alert_type, message, related_entity=None, relation_type=None):
    existing_alert = session.query(Alert).filter(Alert.alert_type == alert_type, Alert.related_entity == related_entity, Alert.relation_type == relation_type, Alert.is_sent == True).first()
    if existing_alert is None:
        users = session.query(User).filter(User.has_access == True).all()
        for user in users:
            try:
                bot.send_message(chat_id=user.telegram_id, text=message)
                new_alert = Alert(alert_type=alert_type, related_entity=related_entity, relation_type=relation_type, is_sent=True)
                session.add(new_alert)
                session.commit()
            except BadRequest as e:
                print(f"Failed to send message to user {user.telegram_id}: {e.message}")



def check_for_new_big_positions():
    positions = session.query(Position).filter(Position.position_cost > 1000000, Position.open_time > datetime.utcnow().replace(tzinfo=pytz.UTC)).all()
    for position in positions:
        message = "🔔 Big Position Alert! A new position has been opened with a high cost. This could indicate a significant move in the market. Here are the details:\n\n" + format_position(position)
        send_alert_to_users("new_big_position", position.id, message)

def check_for_closed_big_positions():
    positions = session.query(Position).filter(Position.position_cost > 1000000, Position.close_time > datetime.utcnow().replace(tzinfo=pytz.UTC)).all()
    for position in positions:
        message = "🔔 Big Position Alert! A position with a high cost has been closed. This could indicate a significant move in the market. Here are the details:\n\n" + format_position(position)
        send_alert_to_users("closed_big_position", position.id, message)

def check_for_same_symbol_positions():
    positions = session.query(Position.symbol, func.count(Position.id)).group_by(Position.symbol).having(func.count(Position.id) > 5).all()
    for symbol, count in positions:
        # Get the direction of the majority of the positions
        long_positions = session.query(Position).filter(Position.symbol == symbol, Position.long == True).count()
        short_positions = session.query(Position).filter(Position.symbol == symbol, Position.short == True).count()
        direction = 'up' if long_positions > short_positions else 'down'
        message = f"🔔 Same Symbol Alert! {count} positions have been opened on {symbol} in the last hour. Traders on Binance want the market to move {direction}."
        send_alert_to_users("same_symbol", message, related_entity=symbol, relation_type="symbol")


def check_for_recently_closed_positions():
    one_hour_ago = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(hours=1)
    positions = session.query(Position).filter(Position.close_time > one_hour_ago).order_by(desc(Position.close_time)).limit(5).all()
    if len(positions) >= 5:
        message = "🔔 Many Traders Just Closed Their Positions! This could indicate a significant shift in the market. Here are the details of the recently closed positions:\n\n"
        for position in positions:
            message += format_position(position) + "\n"
        send_alert_to_users("recently_closed_positions", message)


def check_for_high_leverage_positions():
    high_leverage_threshold = 50  # Define what you consider to be high leverage
    positions = session.query(Position).filter(Position.leverage >= high_leverage_threshold, Position.open_time > datetime.utcnow().replace(tzinfo=pytz.UTC)).all()
    for position in positions:
        message = f"🔔 High Leverage Alert! A position with {position.leverage}x leverage has been opened. Here are the details:\n\n" + format_position(position)
        send_alert_to_users("high_leverage", position.id, message)

def check_for_profit_loss_threshold():
    threshold = 100000  # Define your profit/loss threshold
    positions = session.query(Position).filter(func.abs(Position.pnl) >= threshold, Position.close_time > datetime.utcnow().replace(tzinfo=pytz.UTC)).all()
    for position in positions:
        if position.pnl >= 0:
            message = "🔔 Profit Threshold Alert! A position has been closed with a significant profit. This could indicate a successful trade. Here are the details:\n\n" + format_position(position)
        else:
            message = "🔔 Loss Threshold Alert! A position has been closed with a significant loss. This could indicate a trade that didn't go as planned. Here are the details:\n\n" + format_position(position)
        send_alert_to_users("profit_loss_threshold", position.id, message)




def run_position_alerts(context: CallbackContext):
    check_for_new_big_positions()
    check_for_closed_big_positions()
    check_for_same_symbol_positions()
    check_for_recently_closed_positions()
    check_for_high_leverage_positions()
    check_for_profit_loss_threshold()

if __name__ == "__main__":
    run_position_alerts()
