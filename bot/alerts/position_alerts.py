import os
import sys
from sqlalchemy import create_engine, select, desc, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from telegram import Bot
from config.settings import TELEGRAM_API_TOKEN, MY_POSTGRESQL_URL
from bot.database import Position, User
from telegram.ext import CallbackContext

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create a SQLAlchemy session
engine = create_engine(MY_POSTGRESQL_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Initialize the Telegram bot
bot = Bot(token=TELEGRAM_API_TOKEN)

from telegram.error import BadRequest

def send_alert_to_users(message):
    users = session.query(User).filter(User.has_access == True).all()
    for user in users:
        try:
            bot.send_message(chat_id=user.telegram_id, text=message)
        except BadRequest as e:
            print(f"Failed to send message to user {user.telegram_id}: {e.message}")


def check_for_new_big_positions():
    positions = session.query(Position).filter(Position.position_cost > 1000000, Position.open_time > datetime.now()).all()
    for position in positions:
        message = f"Big Position Alert! Position Opened! {position.__dict__}"
        send_alert_to_users(message)

def check_for_closed_big_positions():
    positions = session.query(Position).filter(Position.position_cost > 1000000, Position.close_time > datetime.now()).all()
    for position in positions:
        message = f"Big Position Alert! Position Closed! {position.__dict__}"
        send_alert_to_users(message)

def check_for_same_symbol_positions():
    positions = session.query(Position.symbol, func.count(Position.id)).group_by(Position.symbol).having(func.count(Position.id) > 5).all()
    for symbol, count in positions:
        message = f"Traders Seem To Agree on {symbol} moving {'up' if Position.long else 'down'}.\n{count} positions open."
        send_alert_to_users(message)

def check_for_recently_closed_positions():
    positions = session.query(Position).filter(Position.close_time > datetime.now()).order_by(desc(Position.close_time)).limit(5).all()
    if len(positions) >= 5:
        message = "Many Traders Just Closed Their Positions!\n"
        for position in positions:
            message += f"{position.__dict__}\n"
        send_alert_to_users(message)

def run_position_alerts(context: CallbackContext):
    check_for_new_big_positions()
    check_for_closed_big_positions()
    check_for_same_symbol_positions()
    check_for_recently_closed_positions()

if __name__ == "__main__":
    run_position_alerts()
