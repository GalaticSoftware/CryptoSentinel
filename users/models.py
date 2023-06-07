from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# User table class definition
class User(Base):
    __tablename__ = "users"  # Define the table name
    id = Column(Integer, primary_key=True)  # Primary key
    telegram_id = Column(Integer, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)
    subscription_end = Column(DateTime)  # Subscription end date
    subscription_type = Column(String)  # Subscription type
    referrer_id = Column(Integer) # Referrer's Telegram ID
    used_referral_code = Column(String) # has already used a referral code - (yes, no) - default: no



