from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, func, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config.settings import MY_POSTGRESQL_URL

# Create a declarative base class for creating table classes
Base = declarative_base()

# User table class definition
class User(Base):
    __tablename__ = 'users'  # Define the table name
    id = Column(Integer, primary_key=True)  # Primary key
    telegram_id = Column(Integer, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)
    subscription_end = Column(DateTime)  # Subscription end date
    subscription_type = Column(String)  # Subscription type

# One Time Token table class definition
class OneTimeToken(Base):
    __tablename__ = 'tokens'
    token = Column(String, primary_key=True)
    expiration_time = Column(DateTime)
    used = Column(Boolean, default=False)
    access_duration = Column(String)  # Access duration (one_month, three_months, yearly, or lifetime)


# Summary table class definition
class SummaryData(Base):
    __tablename__ = 'summary_history'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_whale_longs = Column(Numeric(20, 2), nullable=False)
    total_whale_shorts = Column(Numeric(20, 2), nullable=False)
    total_retail_longs = Column(Numeric(20, 2), nullable=False)
    total_retail_shorts = Column(Numeric(20, 2), nullable=False)


# Command Usage table class definition
class CommandUsage(Base):
    __tablename__ = 'command_usage'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.telegram_id'), nullable=False)
    command_name = Column(String, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # Add this line
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

# Position table class definition
class Position(Base):
    __tablename__ = 'positions'
    id = Column(String, primary_key=True)  # unique identifier for each position
    trader_id = Column(String, nullable=False)  # trader UID
    symbol = Column(String, nullable=False)  # symbol
    entry_price = Column(Numeric(20, 10), nullable=False)  # entry price
    mark_price = Column(Numeric(20, 10), nullable=False)  # mark price
    pnl = Column(Numeric(20, 10), nullable=False)  # pnl
    roe = Column(Numeric(20, 10), nullable=False)  # roe
    amount = Column(Numeric(20, 10), nullable=False)  # amount
    update_timestamp = Column(BigInteger, nullable=False)  # update timestamp
    trade_before = Column(Boolean, nullable=False)  # traded before
    long = Column(Boolean, nullable=False)  # is long
    short = Column(Boolean, nullable=False)  # is short
    leverage = Column(Integer, nullable=False)  # leverage
    position_cost = Column(Numeric(20, 10), nullable=False)  # position cost
    current_position_value = Column(Numeric(20, 10), nullable=False)  # current position value
    open_time = Column(DateTime, nullable=False)  # open time
    close_time = Column(DateTime)  # close time
    profit_or_loss = Column(String)  # profit or loss
    consecutive_absences = Column(Integer, default=0)  # consecutive absences

# Alert table class definition
class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)  # unique identifier for each alert
    alert_type = Column(String, nullable=False)  # type of the alert
    related_entity = Column(String)  # related entity (either a position id or a symbol)
    relation_type = Column(String)  # type of the relation (either 'position' or 'symbol')
    sent_at = Column(DateTime, default=func.now())  # when the alert was sent
    is_sent = Column(Boolean, default=False)  # if the alert has been sent

# Fetched Position table class definition
class FetchedPosition(Base):
    __tablename__ = 'fetched_positions'
    id = Column(Integer, primary_key=True)  # unique identifier for each position
    uid = Column(String, nullable=False)  # trader UID
    symbol = Column(String, nullable=False)  # symbol
    entry_price = Column(Numeric(20, 10), nullable=False)  # entry price
    mark_price = Column(Numeric(20, 10), nullable=False)  # mark price
    pnl = Column(Numeric(20, 10), nullable=False)  # pnl
    roe = Column(Numeric(20, 10), nullable=False)  # roe
    amount = Column(Numeric(20, 10), nullable=False)  # amount
    update_timestamp = Column(BigInteger, nullable=False)  # update timestamp
    trade_before = Column(Boolean, nullable=False)  # traded before
    long = Column(Boolean, nullable=False)  # is long
    short = Column(Boolean, nullable=False)  # is short
    leverage = Column(Integer, nullable=False)  # leverage
    opened_at = Column(DateTime, default=datetime.utcnow)  # when the position was opened
    closed_at = Column(DateTime)  # when the position was closed



# Create a connection to the database and bind the engine
engine = create_engine(MY_POSTGRESQL_URL)

# Create all tables (if they don't already exist) in the database
Base.metadata.create_all(engine)

# Create a session factory for creating sessions to interact with the database
Session = sessionmaker(bind=engine)
