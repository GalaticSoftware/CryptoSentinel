import asyncio
import ccxt
import datetime
import logging
import os
import pandas as pd
import psycopg2
import schedule
import sys
import ta
import ta.volume
from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands, AverageTrueRange

# Append parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MY_POSTGRESQL_URL

Base = declarative_base()

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

TIMEFRAME = '1h'

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.signals = []

    async def fetch_and_store_data(self):
        # Fetch the latest datetime for the symbol from the database
        latest_candle = session.query(OHLCV).filter(OHLCV.symbol == self.symbol).order_by(OHLCV.datetime.desc()).first()
        latest_datetime = latest_candle.datetime if latest_candle else None

        exchange = ccxt.bybit({
            'timeout': 30000,
            'enableRateLimit': True,
        })

        data = exchange.fetch_ohlcv(self.symbol, TIMEFRAME)

        # Store data in the database
        for candle in data:
            timestamp = datetime.datetime.fromtimestamp(candle[0] / 1000)  # Convert milliseconds to seconds

            # Check if the candle's datetime is newer than the latest recorded datetime
            if latest_datetime is None or timestamp > latest_datetime:
                ohlcv = OHLCV(
                    symbol=self.symbol,
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

    def calculate_indicators(self):
        # Fetch data for this symbol from the database
        data = pd.read_sql(session.query(OHLCV).filter(OHLCV.symbol == self.symbol).order_by(OHLCV.datetime).statement, session.bind)

        # Calculate indicators
        data['sma_50'] = SMAIndicator(data['close'], window=50).sma_indicator()
        data['sma_200'] = SMAIndicator(data['close'], window=200).sma_indicator()
        data['rsi'] = RSIIndicator(data['close']).rsi()

        macd_indicator = MACD(data['close'])
        data['macd'] = macd_indicator.macd()
        data['macd_signal'] = macd_indicator.macd_signal()
        data['macd_histogram'] = macd_indicator.macd_diff()

        stoch_osc = StochasticOscillator(data['high'], data['low'], data['close'])
        data['stoch_k'] = stoch_osc.stoch()
        data['stoch_d'] = stoch_osc.stoch_signal()

        bollinger = BollingerBands(data['close'])
        data['bb_high'] = bollinger.bollinger_hband()
        data['bb_mid'] = bollinger.bollinger_mavg()
        data['bb_low'] = bollinger.bollinger_lband()

        data['atr'] = AverageTrueRange(data['high'], data['low'], data['close']).average_true_range()

        return data
    
    

    def check_signals(self, data):
        # Iterate through each row of data
        for index, row in data.iterrows():
            if index > 0:  # Ensure we have a previous row for comparison
                last_row = data.iloc[index - 1]
                
                # Check SMA crossover
                if last_row['sma_50'] < last_row['sma_200'] and row['sma_50'] > row['sma_200']:
                    message = f'{self.symbol}: Bullish signal - SMA 50 crossed above SMA 200.'
                    self.signals.append(message)
                elif last_row['sma_50'] > last_row['sma_200'] and row['sma_50'] < row['sma_200']:
                    message = f'{self.symbol}: Bearish signal - SMA 50 crossed below SMA 200.'
                    self.signals.append(message)

                # Check RSI
                if last_row['rsi'] >= 70 and row['rsi'] < 70:
                    message = f'{self.symbol}: Sell signal - RSI crossed below 70 from overbought territory.'
                    self.signals.append(message)
                elif last_row['rsi'] <= 30 and row['rsi'] > 30:
                    message = f'{self.symbol}: Buy signal - RSI crossed above 30 from oversold territory.'
                    self.signals.append(message)

                # Check MACD
                if last_row['macd'] < last_row['macd_signal'] and row['macd'] > row['macd_signal']:
                    message = f'{self.symbol}: Bullish signal - MACD line crossed above signal line.'
                    self.signals.append(message)
                elif last_row['macd'] > last_row['macd_signal'] and row['macd'] < row['macd_signal']:
                    message = f'{self.symbol}: Bearish signal - MACD line crossed below signal line.'
                    self.signals.append(message)

                # Check Stochastic Oscillator
                if last_row['stoch_k'] < last_row['stoch_d'] and row['stoch_k'] > row['stoch_d']:
                    message = f'{self.symbol}: Buy signal - Stochastic %K crossed above %D.'
                    self.signals.append(message)
                elif last_row['stoch_k'] > last_row['stoch_d'] and row['stoch_k'] < row['stoch_d']:
                    message = f'{self.symbol}: Sell signal - Stochastic %K crossed below %D.'
                    self.signals.append(message)

                # Check Bollinger Bands
                if last_row['close'] <= last_row['bb_low'] and row['close'] > row['bb_low']:
                    message = f'{self.symbol}: Buy signal - Price crossed above lower Bollinger Band.'
                    self.signals.append(message)
                elif last_row['close'] >= last_row['bb_high'] and row['close'] < row['bb_high']:
                    message = f'{self.symbol}: Sell signal - Price crossed below upper Bollinger Band.'
                    self.signals.append(message)

    async def process(self):
        try:
            await self.fetch_and_store_data()
            data = self.calculate_indicators()
            self.check_signals(data)
        except Exception as e:
            logging.exception(f'Error processing {self.symbol}: {e}')
        finally:
            return self.signals

async def main():
    symbols = ['BTC/USDT', 'ETH/USDT']

    for symbol in symbols:
        stock = Stock(symbol)
        signals = await stock.process()
        for signal in signals:
            print(signal)
            
if __name__ == '__main__':
    asyncio.run(main())
