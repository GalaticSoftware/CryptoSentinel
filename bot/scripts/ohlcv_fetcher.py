import ccxt
from sqlalchemy.orm import Session, sessionmaker, scoped_session, relationship
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from config.settings import MY_POSTGRESQL_URL
from datetime import datetime
from bot.database import OHLCVData
import time

# Create a declarative base class for creating table classes
Base = declarative_base()
# setup database connection
engine = create_engine(MY_POSTGRESQL_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)

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


    def fetch_and_store_ohlcv_data(symbols):
        exchange = ccxt.binance()

        session = Session()

        for symbol in symbols:
            try:
                print(f"Fetching OHLCV data for {symbol}...")
                ohlcv_data = exchange.fetch_ohlcv(symbol, '1h')

                for data in ohlcv_data:
                    timestamp, open, high, low, close, volume = data
                    ohlcv = OHLCVData(
                        symbol=symbol,
                        timestamp=datetime.utcfromtimestamp(timestamp // 1000),
                        open=open,
                        high=high,
                        low=low,
                        close=close,
                        volume=volume
                    )

                    session.add(ohlcv)
                    session.commit()

                print(f"Stored OHLCV data for {symbol}")

            except Exception as e:
                print(f"Failed to fetch OHLCV data for {symbol}. Error: {e}")

            time.sleep(exchange.rateLimit / 1000)  # Respect the rate limit of the exchange

        session.close()


    def run_fetcher(context=None):
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

        OHLCVData.fetch_and_store_ohlcv_data(symbols)

if __name__ == '__main__':
    OHLCVData.run_fetcher()