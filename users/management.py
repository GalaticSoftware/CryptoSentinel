from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config.settings import MY_POSTGRESQL_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    has_access = Column(Boolean, default=False)
    subscription_end = Column(DateTime)

engine = create_engine(MY_POSTGRESQL_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

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

def check_expired_subscriptions():
    """
    Checks for expired subscriptions and revokes access for those users.
    """
    session = Session()
    current_time = datetime.now()
    expired_users = session.query(User).filter(User.has_access == True, User.subscription_end <= current_time).all()

    for user in expired_users:
        user.has_access = False
        user.subscription_end = None
        session.commit()
    session.close()

def update_user_access(telegram_id, has_access, subscription_end: datetime = None):
    """
    Updates the access status of a user with the given telegram_id.

    Args:
        telegram_id (int): The telegram_id of the user to update.
        has_access (bool): The new access status for the user.
        subscription_end (datetime, optional): The end date of the user's subscription.
    """
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.has_access = has_access
        if subscription_end:
            user.subscription_end = subscription_end
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

