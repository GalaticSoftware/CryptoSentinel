import ta
import pandas as pd
import datetime
from datetime import timedelta, datetime
from sqlalchemy import create_engine, MetaData, Table, select, func, Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import MY_POSTGRESQL_URL
from bot.database import Session, User, OHLCVData
from ta.trend import MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.utils import dropna
from ta.trend import SMAIndicator
from decimal import Decimal
from telegram import Bot
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from telegram import Update
from decimal import Decimal
from config.settings import TELEGRAM_API_TOKEN

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

bot = Bot(token=TELEGRAM_API_TOKEN)

# setup database connection
engine = create_engine(MY_POSTGRESQL_URL)
session_maker = sessionmaker(bind=engine)
Session.configure(bind=engine)

# Setup base
metadata = MetaData()
Base = declarative_base()


# Database table definitions
class OHLCVData(Base):
    __tablename__ = 'ohlcv_data'
    id = Column(Integer, primary_key=True)
    symbol = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    open = Column(Numeric(20, 2), nullable=False)
    high = Column(Numeric(20, 2), nullable=False)
    low = Column(Numeric(20, 2), nullable=False)
    close = Column(Numeric(20, 2), nullable=False)
    volume = Column(Numeric(20, 2), nullable=False)


# Create a class for the indicator alerts
# This class will contain methods for calculating the indicators and checking if the conditions are met
class MarketAlerts:
    # function to fetch the OHLCV data from the database and return it as a dataframe (grouped by symbol)
    @staticmethod
    def fetch_ohlcv_data(symbol):
        session = session_maker()

        # Fetch the OHLCV data from the database
        ohlcv_data = session.query(OHLCVData).filter_by(symbol=symbol).all()

        # Create a dataframe from the OHLCV data
        df = pd.DataFrame(
            [(data.timestamp, data.open, data.high, data.low, data.close, data.volume) for data in ohlcv_data],
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        # Set the timestamp as the index
        df.set_index('timestamp', inplace=True)

        # Drop any rows with NaN values
        df = dropna(df)

        return df

    # Function to calculate all indicators available in the ta library and add them to the dataframe
    @staticmethod
    def calculate_indicators(df):
        try:
            logging.info(f"Calculating indicators for {len(df)} data points.")
            # Check if df is not empty
            if df.empty:
                print("Dataframe is empty.")
                return df
            # Convert Decimal values to float
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)

            # Calculate the indicators
            if 'rsi' not in df.columns:
                print("Column 'rsi' does not exist in df!")
            df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
            df['macd'] = MACD(close=df['close']).macd()
            df['macd_signal'] = MACD(close=df['close']).macd_signal()
            df['macd_diff'] = MACD(close=df['close']).macd_diff()
            df['stoch'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch()
            df['stoch_signal'] = StochasticOscillator(high=df['high'], low=df['low'], close=df['close']).stoch_signal()
            df['bb_bbm'] = BollingerBands(close=df['close']).bollinger_mavg()
            df['bb_bbh'] = BollingerBands(close=df['close']).bollinger_hband()
            df['bb_bbl'] = BollingerBands(close=df['close']).bollinger_lband()
            df['bb_bbhi'] = BollingerBands(close=df['close']).bollinger_hband_indicator()
            df['bb_bbli'] = BollingerBands(close=df['close']).bollinger_lband_indicator()

            window_size = 14
            if len(df) < window_size:
                window_size = len(df)

            # Check if window_size is not 0 before calculating atr
            if window_size > 0:
                df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=window_size).average_true_range()

            df['sma_5'] = SMAIndicator(close=df['close'], window=5).sma_indicator()
            df['sma_10'] = SMAIndicator(close=df['close'], window=10).sma_indicator()
            df['sma_20'] = SMAIndicator(close=df['close'], window=20).sma_indicator()
            df['sma_50'] = SMAIndicator(close=df['close'], window=50).sma_indicator()
            df['sma_100'] = SMAIndicator(close=df['close'], window=100).sma_indicator()
            df['sma_200'] = SMAIndicator(close=df['close'], window=200).sma_indicator()

            return df

        except Exception as e:
            logging.error(f"Error occurred while calculating indicators: {str(e)}")
            # handle or rethrow the exception as per your need


    # Function to check if the conditions for the indicator alerts are met within the latest 2 candles and return a list of the alerts
    # Conditions:
    # RSI comes out of oversold (below 30) and crosses above 30 -> Bullish Signal
    # RSI comes out of overbought (above 70) and crosses below 70 -> Bearish Signal
    # MACD crosses above the signal line -> Bullish Signal
    # MACD crosses below the signal line -> Bearish Signal
    # Stochastic comes out of oversold (below 20) and crosses above 20 -> Bullish Signal
    # Stochastic comes out of overbought (above 80) and crosses below 80 -> Bearish Signal
    # Price crosses above the upper Bollinger Band -> Upside Extension with risk of reversal
    # Price crosses below the lower Bollinger Band -> Downside Extension with risk of reversal
    # Price crosses above the upper Bollinger Band and RSI is above 70 -> Upside Extension with risk of reversal
    # Price crosses below the lower Bollinger Band and RSI is below 30 -> Downside Extension with risk of reversal
    @staticmethod
    def check_indicator_alerts(df):
        try:
            logging.info("Checking indicator alerts.")
            # Create an empty list to store the alerts
            alerts = []

            # Check the conditions for the RSI
            if df['rsi'].iloc[-2] < 30 and df['rsi'].iloc[-1] > 30:
                alerts.append('RSI crossed above 30 (Bullish Signal)')
            if df['rsi'].iloc[-2] > 70 and df['rsi'].iloc[-1] < 70:
                alerts.append('RSI crossed below 70 (Bearish Signal)')

            # Check the conditions for the MACD
            if df['macd'].iloc[-2] < df['macd_signal'].iloc[-2] and df['macd'].iloc[-1] > df['macd_signal'].iloc[-1]:
                alerts.append('MACD crossed above the signal line (Bullish Signal)')
            if df['macd'].iloc[-2] > df['macd_signal'].iloc[-2] and df['macd'].iloc[-1] < df['macd_signal'].iloc[-1]:
                alerts.append('MACD crossed below the signal line (Bearish Signal)')

            # Check the conditions for the Stochastic Oscillator
            if df['stoch'].iloc[-2] < 20 and df['stoch'].iloc[-1] > 20:
                alerts.append('Stochastic Oscillator crossed above 20 (Bullish Signal)')
            if df['stoch'].iloc[-2] > 80 and df['stoch'].iloc[-1] < 80:
                alerts.append('Stochastic Oscillator crossed below 80 (Bearish Signal)')

            # Check the conditions for the Bollinger Bands
            if df['close'].iloc[-2] < df['bb_bbh'].iloc[-2] and df['close'].iloc[-1] > df['bb_bbh'].iloc[-1]:
                alerts.append('Price crossed above the upper Bollinger Band (Potential upside extension)')
            if df['close'].iloc[-2] > df['bb_bbl'].iloc[-2] and df['close'].iloc[-1] < df['bb_bbl'].iloc[-1]:
                alerts.append('Price crossed below the lower Bollinger Band (Potential downside extension)')

            return alerts

        except Exception as e:
            logging.error(f"Error occurred while checking indicator alerts: {str(e)}")
            # handle or rethrow the exception as per your need

    # Function to send the alerts to all users
    @staticmethod
    def send_alerts(context: CallbackContext, alerts, symbol):
        try:
            logging.info(f"Sending {len(alerts)} alerts.")
            # Fetch all the users from the database
            session = session_maker()
            users = session.query(User).all()  # assuming you have a User model in your database

            # Send the alerts to all users
            for user in users:
                try:
                    for alert in alerts:
                        context.bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"🔔 Alert! 🔔\n\n"
                            f"for {symbol} \n\n"
                            f"{alert}"
                        )
                except Exception as e:
                    logging.error(f"Error occurred while sending alert to user {user.telegram_id}: {str(e)}")
        except Exception as e:
            logging.error(f"Error occurred while sending alerts: {str(e)}")



# Function that will be called in main.py to run the bot
# this function will get the data, calculate the indicators, check the conditions and send the alerts
def run_market_alerts(context: CallbackContext):
    # List of symbols to fetch OHLCV data for
    symbols = [
        'BTC/USDT',
        # 'ETH/USDT',
        # 'BNB/USDT',
        # 'XRP/USDT',
        # 'ADA/USDT',
        # 'DOGE/USDT',
        # 'MATIC/USDT',
        # 'SOL/USDT',
        # 'TRX/USDT',
        # 'DOT/USDT',
        # 'LTC/USDT',
        # 'SHIB/USDT',
        # 'AVA/USDT',
        # 'LEO/USDT',
        # 'LINK/USDT',
        # 'ATOM/USDT',
        # 'UNI/USDT',
        # 'OKB/USDT',
        # 'MXR/USDT',
        # 'ETC/USDT',
        # 'TON/USDT',
        # 'XLM/USDT',
        # 'BCH/USDT',
        # 'ICP/USDT',
        # 'HBAR/USDT',
        # 'APT/USDT',
        # 'CRO/USDT',
        # 'NEAR/USDT',
        # 'ARB/USDT',
        # 'VET/USDT',
        # 'QNT/USDT',
        # 'APE/USDT',
        # 'ALGO/USDT',
        # 'GRT/USDT',
        # 'RNDR/USDT',
    ]

    for symbol in symbols:
        try:
            logging.info(f"Running market alerts for {symbol}.")
            # Get the data
            df = MarketAlerts.fetch_ohlcv_data(symbol)

            # Calculate the indicators
            df = MarketAlerts.calculate_indicators(df)

            # Check the conditions and get the alerts
            alerts = MarketAlerts.check_indicator_alerts(df)

            # Send the alerts to all users
            MarketAlerts.send_alerts(context, alerts, symbol)  # Pass the context and symbol arguments here

            # Print the alerts in the console
            print(alerts)
        except Exception as e:
            logging.error(f"Error occurred while running market alerts for {symbol}: {str(e)}")

