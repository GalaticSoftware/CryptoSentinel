from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
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
    telegram_id = Column(Integer, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)
    subscription_end = Column(DateTime)  # Subscription end date
    subscription_type = Column(String)  # Subscription type
    accepted_policy = Column(Boolean, default=False)  # Accepted privacy policy


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
    telegram_id = Column(Integer, unique=True, nullable=False)
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
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    command_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # Add this line
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# Price Alert Request table class definition
class PriceAlertRequest(Base):
    __tablename__ = "price_alert_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.telegram_id"), nullable=False, index=True
    )
    symbol = Column(String, nullable=False, index=True)
    price_level = Column(Numeric(20, 2), nullable=False)


# Define database models
class PatternData(Base):
    __tablename__ = "pattern_data"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    pattern = Column(String, nullable=False)


# Create a connection to the database and bind the engine
engine = create_engine(MY_POSTGRESQL_URL)

# Create all tables (if they don't already exist) in the database
Base.metadata.create_all(engine)

# Create a session factory for creating sessions to interact with the database
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
