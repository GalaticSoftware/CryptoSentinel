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
import asyncio
import psutil
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.telegram_bot import main as telegram_bot_main


from sqlalchemy import Column, Integer, String, DateTime, Numeric, UniqueConstraint, create_engine, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands, AverageTrueRange
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MY_POSTGRESQL_URL, TELEGRAM_API_TOKEN

Base = declarative_base()

class OHLCV(Base):
    __tablename__ = 'ohlcv'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timeframe = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    open = Column(Numeric(20, 10), nullable=False)
    high = Column(Numeric(20, 10), nullable=False)
    low = Column(Numeric(20, 10), nullable=False)
    close = Column(Numeric(20, 10), nullable=False)
    volume = Column(Numeric(20, 10), nullable=False)

    __table_args__ = (UniqueConstraint('symbol', 'timeframe', 'datetime', name='unique_constraint_1'),)


# User table class definition
class User(Base):
    __tablename__ = 'users'  # Define the table name
    id = Column(Integer, primary_key=True)  # Primary key
    telegram_id = Column(Integer, unique=True)  # Unique Telegram ID
    username = Column(String)  # Telegram username
    has_access = Column(Boolean, default=False)  # Access status (default: False)
    subscription_end = Column(DateTime)  # Subscription end date
    subscription_type = Column(String)  # Subscription type



engine = create_engine(MY_POSTGRESQL_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

TIMEFRAME = '1h'

class TelegramNotifier:
    def __init__(self, token):
        self.updater = Updater(token=token, use_context=True)

    def send_message(self, chat_id, message):
        self.updater.bot.send_message(chat_id=chat_id, text=message)

    def start(self):
        self.updater.start_polling()

    def stop(self):
        self.updater.stop()


class Symbol:
    def __init__(self, symbol):
        self.symbol = symbol
        self.signals = []
        self.telegram_notifier = TelegramNotifier(TELEGRAM_API_TOKEN)

    async def fetch_and_store_data(self):
        latest_candle = session.query(OHLCV).filter(OHLCV.symbol == self.symbol).order_by(OHLCV.datetime.desc()).first()
        latest_datetime = latest_candle.datetime if latest_candle else None

        exchange = ccxt.bybit({
            'timeout': 30000,
            'enableRateLimit': True,
        })

        data = exchange.fetch_ohlcv(self.symbol, TIMEFRAME)

        for candle in data:
            timestamp = datetime.datetime.fromtimestamp(candle[0] / 1000)

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
        data = pd.read_sql(session.query(OHLCV).filter(OHLCV.symbol == self.symbol).order_by(OHLCV.datetime).statement, session.bind)

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
        for index, row in data.iterrows():
            if index > 0:  # Ensure we have a previous row for comparison
                last_row = data.iloc[index - 1]

                # Initialize the message variable with a default value
                message = None

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

                # Send the signal to all users on Telegram
                if message:
                    for user in session.query(User).all():
                        self.telegram_notifier.send_message(user.telegram_id, message)


    async def process(self):
        try:
            await self.fetch_and_store_data()
            data = self.calculate_indicators()
            self.check_signals(data)
        except Exception as e:
            logging.exception(f'Error processing {self.symbol}: {e}')
        finally:
            return self.signals

def run_fetcher_script():
    symbols = ['BTC/USDT', 'ETH/USDT']

    for symbol in symbols:
        stock = Symbol(symbol)
        asyncio.run(stock.fetch_and_store_data())
        data = stock.calculate_indicators()
        stock.check_signals(data)

def main() -> None:
    # Schedule the job to run the fetcher script every hour
    schedule.every().hour.do(run_fetcher_script)

    # Start the scheduler
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error("An error occurred: %s", str(e))

if __name__ == '__main__':
    # Stop any existing instances of the Telegram bot
    for proc in psutil.process_iter():
        try:
            if "python" in proc.name() and "main.py" in proc.cmdline():
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Start the Telegram bot
    telegram_bot_task = asyncio.create_task(telegram_bot_main())

    # Start the main loop
    main_task = asyncio.create_task(main())

    # Run the event loop
    try:
        asyncio.run(asyncio.wait([telegram_bot_task, main_task]))
    except Exception as e:
        logging.error("An error occurred: %s", str(e))