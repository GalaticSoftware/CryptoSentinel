from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config.settings import DATABASE_URL

# Create a declarative base class for creating table classes
Base = declarative_base()

# User table class definition
class User(Base):
    __tablename__ = 'users'  # Define the table name
    id = Column(Integer, primary_key=True)  # Primary key
    telegram_id = Column(Integer, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)

# One Time Token table class definition
class OneTimeToken(Base):
    __tablename__ = 'tokens'
    token = Column(String, primary_key=True)
    expiration_time = Column(DateTime)
    used = Column(Boolean, default=False)

# Summary table class definition
class SummaryData(Base):
    __tablename__ = 'summary_history'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_whale_longs = Column(Numeric(20, 2), nullable=False)
    total_whale_shorts = Column(Numeric(20, 2), nullable=False)
    total_retail_longs = Column(Numeric(20, 2), nullable=False)
    total_retail_shorts = Column(Numeric(20, 2), nullable=False)

# Create a connection to the database and bind the engine
engine = create_engine(DATABASE_URL)

# Create all tables (if they don't already exist) in the database
Base.metadata.create_all(engine)

# Create a session factory for creating sessions to interact with the database
Session = sessionmaker(bind=engine)
