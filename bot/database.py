from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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

# Create a connection to the database and bind the engine
engine = create_engine(DATABASE_URL)

# Create all tables (if they don't already exist) in the database
Base.metadata.create_all(engine)

# Create a session factory for creating sessions to interact with the database
Session = sessionmaker(bind=engine)
