from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import MY_POSTGRESQL_URL
from telegram.ext import CallbackContext
from database.models import User

Base = declarative_base()

engine = create_engine(MY_POSTGRESQL_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

import logging
logger = logging.getLogger(__name__)

def get_or_create_user(telegram_id, username):
    """
    Retrieves or creates a user with the given telegram_id and username.

    Args:
        telegram_id (int): The telegram_id of the user.
        username (str): The username of the user.

    Returns:
        user (User): The retrieved or newly created User instance.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        session.commit()
    session.close()
    return user

def check_user_access(telegram_id):
    """
    Checks if a user with the given telegram_id has access to the bot's features.

    Args:
        telegram_id (int): The telegram_id of the user to check.

    Returns:
        bool: True if the user has access, False otherwise.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user and user.has_access

def check_user_policy_status(telegram_id):
    """
    Checks if a user with the given telegram_id has accepted the privacy policy.

    Args:
        telegram_id (int): The telegram_id of the user to check.

    Returns:
        bool: True if the user has accepted the privacy policy, False otherwise.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user and user.accepted_policy

def check_expired_subscriptions(context: CallbackContext):
    """
    Checks for expired subscriptions and revokes access for those users.
    """
    logger.info("Checking for expired subscriptions...")
    print("Checking for expired subscriptions...")

    session = Session()
    current_time = datetime.now()
    expired_users = session.query(User).filter(User.has_access == True, User.subscription_end <= current_time).all()

    for user in expired_users:
        user.has_access = False
        user.subscription_end = None
        session.commit()
        context.bot.send_message(chat_id=user.username, text=f"Revoked access for user {user.username}.")
        logger.info(f"Revoked access for user {user.username}.")
        print(f"Revoked access for user {user.username}.")
    session.close()






def update_user_access(telegram_id, has_access, subscription_end: datetime = None, subscription_type: str = None):
    """
    Updates the access status and subscription type of a user with the given telegram_id.

    Args:
        telegram_id (int): The telegram_id of the user to update.
        has_access (bool): The new access status for the user.
        subscription_end (datetime, optional): The end date of the user's subscription.
        subscription_type (str, optional): The subscription type for the user.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.has_access = has_access
        if subscription_end:
            user.subscription_end = subscription_end
        if subscription_type:
            user.subscription_type = subscription_type
        session.commit()
    session.close()


def revoke_user_access(telegram_id):
    """
    Revokes the access status of a user with the given telegram_id.

    Args:
        telegram_id (int): The telegram_id of the user to update.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.has_access = False
        user.subscription_end = None
        session.commit()
    session.close()
