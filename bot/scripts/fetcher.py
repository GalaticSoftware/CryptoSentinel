from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import requests
from datetime import datetime
import hashlib

from config.settings import X_RAPIDAPI_KEY
from config.settings import MY_POSTGRESQL_URL

# Set up database
engine = create_engine(MY_POSTGRESQL_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Define database models
class PatternData(Base):
    __tablename__ = "pattern_data"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    pattern = Column(String, nullable=False)

# Create database tables if they don't exist
Base.metadata.create_all(engine)

def fetch_pattern_data(context=None):
    symbols = ["BTCUSDT", "ETHUSDT", "LTCUSDT", "AVAXUSDT", "DOTUSDT"]
    url = "https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/patterns/{}/4h"
    headers = {
        "X-RapidAPI-Key":  X_RAPIDAPI_KEY,
        "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com"
    }

    session = Session()

    for symbol in symbols:
        response = requests.get(url.format(symbol), headers=headers)
        data = response.json()

        timestamp = datetime.fromtimestamp(data['timestamp'] / 1000)
        timeframe = data['timeframe']

        for pattern, is_present in data.items():
            if pattern not in ['timestamp', 'symbol', 'timeframe', 'prices'] and is_present:
                id = hashlib.md5(f"{timestamp}{symbol}{pattern}".encode()).hexdigest()

                # Check if a record with the same ID already exists
                exists = session.query(PatternData.id).filter_by(id=id).scalar() is not None

                if not exists:
                    pattern_data = PatternData()
                    pattern_data.id = id
                    pattern_data.timestamp = timestamp
                    pattern_data.symbol = symbol
                    pattern_data.timeframe = timeframe
                    pattern_data.pattern = pattern

                    session.add(pattern_data)

    session.commit()



if __name__ == "__main__":
    fetch_pattern_data()