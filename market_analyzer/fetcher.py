import ccxt
import psycopg2
import asyncio
from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
import ta
import ta.volume

import pandas as pd

Base = declarative_base()

import sys
import os

# Append parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MY_POSTGRESQL_URL
import schedule
import time

# OHLCV table class definition
class OHLCV(Base):
    __tablename__ = 'ohlcv'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)  # Updated column name
    open = Column(Numeric(20, 10), nullable=False)
    high = Column(Numeric(20, 10), nullable=False)
    low = Column(Numeric(20, 10), nullable=False)
    close = Column(Numeric(20, 10), nullable=False)
    volume = Column(Numeric(20, 10), nullable=False)

    __table_args__ = (UniqueConstraint('symbol', 'timeframe', 'datetime', name='unique_constraint_1'),)


# Create the engine and session
engine = create_engine(MY_POSTGRESQL_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


SYMBOLS = [
    'BTC/USDT',
    'ETH/USDT',
    'BNB/USDT',
    'XRP/USDT',
    'ADA/USDT',
    'DOGE/USDT',
    'MATIC/USDT',
    'SOL/USDT',
    'TRX/USDT',
    'LTC/USDT',
    ]

TIMEFRAME = '15m'

async def fetch_and_store_data(symbol):
    # Fetch the latest datetime for the symbol from the database
    latest_candle = session.query(OHLCV).filter(OHLCV.symbol == symbol).order_by(OHLCV.datetime.desc()).first()
    latest_datetime = latest_candle.datetime if latest_candle else None

    exchange = ccxt.bybit({
        'timeout': 30000,
        'enableRateLimit': True,
    })

    data = exchange.fetch_ohlcv(symbol, TIMEFRAME)

    # Store data in the database
    for candle in data:
        timestamp = datetime.datetime.fromtimestamp(candle[0] / 1000)  # Convert milliseconds to seconds

        # Check if the candle's datetime is newer than the latest recorded datetime
        if latest_datetime is None or timestamp > latest_datetime:
            ohlcv = OHLCV(
                symbol=symbol,
                timeframe=TIMEFRAME,
                datetime=timestamp,
                open=candle[1],
                high=candle[2],
                low=candle[3],
                close=candle[4],
                volume=candle[5]
            )
            session.add(ohlcv)

    session.commit()



# Dictionary to store indicator signals
indicator_signals = {}

# Function to calculate indicators
def calculate_indicators(symbol):
    # Fetch the OHLCV data for the symbol from the database
    query = session.query(OHLCV).filter(OHLCV.symbol == symbol).order_by(OHLCV.datetime.asc())
    data = [(candle.datetime, candle.high, candle.low, candle.close, candle.volume) for candle in query]

    # Extract the OHLCV data into separate lists
    timestamps = [candle[0] for candle in data]
    highs = [candle[1] for candle in data]
    lows = [candle[2] for candle in data]
    closes = [candle[3] for candle in data]
    volumes = [candle[4] for candle in data]

    # Convert the OHLCV lists to pandas Series
    high_series = pd.Series(highs)
    low_series = pd.Series(lows)
    close_series = pd.Series(closes)
    volume_series = pd.Series(volumes)

    # Calculate the indicators
    acc_dist_index = ta.volume.AccDistIndexIndicator(high_series, low_series, close_series, volume_series)
    ease_of_movement = ta.volume.EaseOfMovementIndicator(high_series, low_series, volume_series)
    on_balance_volume = ta.volume.OnBalanceVolumeIndicator(close_series, volume_series)

    # Get the indicator values
    acc_dist_values = acc_dist_index.acc_dist_index()
    ease_of_movement_values = ease_of_movement.ease_of_movement()
    on_balance_volume_values = on_balance_volume.on_balance_volume()

    # Store the indicator signals in the dictionary
    indicator_signals[symbol] = {
        'acc_dist_index': acc_dist_values,
        'ease_of_movement': ease_of_movement_values,
        'on_balance_volume': on_balance_volume_values
    }

    # Print the indicator signals for each symbol
    print(f"{symbol} Signals:")
    if on_balance_volume_values.iloc[-1] > on_balance_volume_values.iloc[-2] > on_balance_volume_values.iloc[-3]:
        print(f"OnBalanceVolume (OBV) increasing. This suggests accumulating volume for {symbol}")
    else:
        print(f"OnBalanceVolume (OBV) not increasing for {symbol}")


async def job():
    for symbol in SYMBOLS:
        await fetch_and_store_data(symbol)
        calculate_indicators(symbol)
        print(f"Data fetched and indicators calculated for {symbol}")


async def main():
    # Run initial data fetching
    await job()
    print("Initial data fetching and indicator calculation completed.")

    # Schedule job to run every 15 minutes
    schedule.every(15).minutes.do(job)
    print("Job scheduled.")

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# Run the main function
asyncio.run(main())
