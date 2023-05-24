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
from ta.momentum import RSIIndicator, MACD, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.trend import SMAIndicator


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

### Define and Calculate Indicators ###
def calculate_rsi(close_series, period=14):
    rsi = RSIIndicator(close_series, period)
    return rsi.rsi()

def calculate_macd(close_series, short_period=12, long_period=26, signal_period=9):
    macd = MACD(close_series, short_period, long_period, signal_period)
    return macd.macd_diff()

def calculate_bollinger_bands(close_series, n=20, ndev=2):
    bollinger = BollingerBands(close_series, n, ndev)
    return bollinger.bollinger_hband_indicator(), bollinger.bollinger_lband_indicator()

def calculate_atr(high_series, low_series, close_series, n=14):
    atr = AverageTrueRange(high_series, low_series, close_series, n)
    return atr.average_true_range()

def calculate_sma(close_series, short_window=50, long_window=200):
    short_sma = SMAIndicator(close_series, short_window).sma_indicator()
    long_sma = SMAIndicator(close_series, long_window).sma_indicator()
    return short_sma, long_sma

def calculate_stochastic(high_series, low_series, close_series, n=14, d_n=3):
    stochastic = StochasticOscillator(high_series, low_series, close_series, n, d_n)
    return stochastic.stoch()


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
    rsi_values = calculate_rsi(close_series)
    macd_values = calculate_macd(close_series)
    bb_upper, bb_lower = calculate_bollinger_bands(close_series)
    atr_values = calculate_atr(high_series, low_series, close_series)
    short_sma_values, long_sma_values = calculate_sma(close_series)
    stochastic_values = calculate_stochastic(high_series, low_series, close_series)

    # Get the indicator values
    acc_dist_values = acc_dist_index.acc_dist_index()
    ease_of_movement_values = ease_of_movement.ease_of_movement()
    on_balance_volume_values = on_balance_volume.on_balance_volume()

    # Store the new indicator signals in the dictionary
    indicator_signals[symbol].update({
        'rsi': rsi_values,
        'macd': macd_values,
        'bb_upper': bb_upper,
        'bb_lower': bb_lower,
        'atr': atr_values,
        'short_sma': short_sma_values,
        'long_sma': long_sma_values,
        'stochastic': stochastic_values
    })

    # Check for significant signals
    significant_signals = []

    if on_balance_volume_values.iloc[-1] > on_balance_volume_values.iloc[-2] > on_balance_volume_values.iloc[-3]:
        significant_signals.append(f"On-Balance Volume (OBV) is increasing. This suggests accumulating volume for {symbol}.\nIncreasing OBV: If the OBV is increasing, it suggests that there is a higher volume associated with upward price movements. This indicates buying pressure and suggests that traders are accumulating the asset, which could be seen as a bullish signal.")

    if acc_dist_values.iloc[-1] > 0:
        significant_signals.append(f"Accumulation Distribution Index (ADI) is positive for {symbol}.\nPositive ADI: If the ADI is positive, it suggests that there is more buying pressure in the asset. This indicates that the asset is being accumulated by traders, which could be seen as a bullish signal.")

    if ease_of_movement_values.iloc[-1] > 0:
        significant_signals.append(f"Ease of Movement (EOM) is positive for {symbol}.\nPositive EOM: If the EOM is positive, it suggests that there is a positive relationship between price changes and volume. This indicates that the asset is experiencing upward price movement with relatively low volume, which could be seen as a bullish signal.")

    # Check for MACD signals
    if macd_values.iloc[-1] > 0 and macd_values.iloc[-2] <= 0:
        significant_signals.append(f"MACD line crossed above the signal line, indicating bullish conditions for {symbol}.")

    if macd_values.iloc[-1] < 0 and macd_values.iloc[-2] >= 0:
        significant_signals.append(f"MACD line crossed below the signal line, indicating bearish conditions for {symbol}.")

    # Check for Bollinger Bands signals
    if bb_upper.iloc[-1] > 0 and bb_upper.iloc[-2] <= 0:
        significant_signals.append(f"Price crossed above the upper Bollinger Band, indicating a potential upper band breakout for {symbol}.")

    if bb_lower.iloc[-1] > 0 and bb_lower.iloc[-2] <= 0:
        significant_signals.append(f"Price crossed below the lower Bollinger Band, indicating a potential lower band breakout for {symbol}.")

    # Check for ATR signals
    if atr_values.iloc[-1] > atr_values.mean():
        significant_signals.append(f"ATR value exceeds its average, indicating high volatility for {symbol}.")

    # Check for SMA signals
    if short_sma_values.iloc[-1] > long_sma_values.iloc[-1] and short_sma_values.iloc[-2] <= long_sma_values.iloc[-2]:
        significant_signals.append(f"Short-term SMA crossed above long-term SMA, indicating a golden cross for {symbol}.")

    if short_sma_values.iloc[-1] < long_sma_values.iloc[-1] and short_sma_values.iloc[-2] >= long_sma_values.iloc[-2]:
        significant_signals.append(f"Short-term SMA crossed below long-term SMA, indicating a death cross for {symbol}.")

    # Check for Stochastic Oscillator signals
    if stochastic_values.iloc[-1] > 80:
        significant_signals.append(f"Stochastic Oscillator value is above 80, indicating overbought conditions for {symbol}.")

    if stochastic_values.iloc[-1] < 20:
        significant_signals.append(f"Stochastic Oscillator value is below 20, indicating oversold conditions for {symbol}.")

    # Print the signals if there are any significant signals
    if significant_signals:
        print(f"{symbol} Signals:")
        for signal in significant_signals:
            print(signal)
    else:
        print(f"No significant signals found for {symbol}.")
        print()



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
