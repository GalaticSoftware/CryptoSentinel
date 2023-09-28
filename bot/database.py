from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey,
    func,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config.settings import MY_POSTGRESQL_URL

# Create a declarative base class for creating table classes
Base = declarative_base()


# User table class definition
class User(Base):
    __tablename__ = "users"  # Define the table name
    id = Column(Integer, primary_key=True)  # Primary key
    telegram_id = Column(BigInteger, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)
    subscription_end = Column(DateTime)  # Subscription end date
    subscription_type = Column(String)  # Subscription type
    referrer_id = Column(Integer) # Referrer's Telegram ID
    used_referral_code = Column(String, default="no") # has already used a referral code - (yes, no) - default: no


# One Time Token table class definition
class OneTimeToken(Base):
    __tablename__ = "tokens"
    token = Column(String, primary_key=True)
    expiration_time = Column(DateTime)
    used = Column(Boolean, default=False)
    access_duration = Column(
        String
    )  # Access duration (one_month, three_months, yearly, or lifetime)


# Waiting List table class definition
class WaitingList(Base):
    __tablename__ = "waiting_list"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    join_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# Summary table class definition
class SummaryData(Base):
    __tablename__ = "summary_history"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_whale_longs = Column(Numeric(20, 2), nullable=False)
    total_whale_shorts = Column(Numeric(20, 2), nullable=False)
    total_retail_longs = Column(Numeric(20, 2), nullable=False)
    total_retail_shorts = Column(Numeric(20, 2), nullable=False)


# Command Usage table class definition
class CommandUsage(Base):
    __tablename__ = "command_usage"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    command_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # Add this line
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# Price Alert Request table class definition
class PriceAlertRequest(Base):
    __tablename__ = "price_alert_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        BigInteger, ForeignKey("users.telegram_id"), nullable=False, index=True
    )
    symbol = Column(String, nullable=False, index=True)
    price_level = Column(Numeric(20, 2), nullable=False)

    

class PatternData(Base):
    __tablename__ = "pattern_data"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    pattern = Column(String, nullable=False)


class ReferralCodes(Base):
    __tablename__ = "referral_codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)  # Changed from "users.telegram_id" to "users.id"
    code = Column(String, nullable=False)


class Referrals(Base):
    __tablename__ = "referrals"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False) # Referrer's Telegram ID
    referral_code = Column(String, nullable=False) # Referral code used
    referred_user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False) # Referred user's Telegram ID
    referred_user_username = Column(String, nullable=False) # Referred user's Telegram username
    status = Column(String, nullable=False) # Status of the referral - membership status of the referred user - (active, expired, cancelled)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False) # Timestamp of the referral


# Create a connection to the database and bind the engine
engine = create_engine(MY_POSTGRESQL_URL)

# Create all tables (if they don't already exist) in the database
Base.metadata.create_all(engine)

# Create a session factory for creating sessions to interact with the database
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
