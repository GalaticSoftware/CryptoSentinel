from telegram import Update
from telegram.ext import CallbackContext
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, DateTime
from bot.database import OneTimeToken, User, Base
from bot.utils import restricted
from datetime import datetime

# Import the database URL from the settings
from config.settings import DATABASE_URL

# logging
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
            logger.debug("Usage message sent")
            return

        token = args[0]
        session = Session()
        existing_token = session.query(OneTimeToken).filter_by(token=token).first()

        logger.debug("Token information: %s", existing_token)

        if existing_token and existing_token.expiration_time > datetime.utcnow() and not existing_token.used:
            logger.debug("Inside condition: existing_token.used = %s", existing_token.used)
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
                logger.debug("Token used status updated: existing_token.used = %s", existing_token.used)
                update.message.reply_text("Access granted! Your token has been successfully used.")
                logger.debug("Access granted message sent.")
            else:
                update.message.reply_text("User not found. Please try again.")
                logger.debug("User not found message sent.")
        else:
            update.message.reply_text("Invalid or expired token. Please try again.")
            logger.debug("Invalid or expired token message sent.")
        session.close()


