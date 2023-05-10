from telegram import Update
from telegram.ext import CallbackContext
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, DateTime
from bot.database import OneTimeToken, User, Base
from bot.utils import restricted
from datetime import datetime

# Import the database URL from the settings
from config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

class UseTokenHandler:
    @staticmethod
    def use_token(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        username = update.effective_user.username
        args = context.args

        if len(args) != 1:
            update.message.reply_text("Usage: /use_token <your_token>")
            return

        token = args[0]
        session = Session()
        existing_token = session.query(OneTimeToken).filter_by(token=token).first()

        if existing_token and existing_token.expiration_time > datetime.utcnow() and not existing_token.used:
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                # Create a new user if not found
                user = User(telegram_id=user_id, username=username, has_access=False)
                session.add(user)
                session.commit()
                user = session.query(User).filter_by(telegram_id=user_id).first()

            if user:
                user.has_access = True
                existing_token.used = True  # Mark the token as used
                session.commit()
                update.message.reply_text("Access granted! Your token has been successfully used.")
            else:
                update.message.reply_text("User not found. Please try again.")
        else:
            update.message.reply_text("Invalid or expired token. Please try again.")
        session.close()


