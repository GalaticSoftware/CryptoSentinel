import ccxt
import time
from datetime import datetime
from decimal import Decimal
from bot.database import OHLCV, Session
from telegram.ext import CallbackContext

class OHLCVFetcher:
    def fetch_ohlcv_data(context: CallbackContext):
        # Initialize the exchanges
        exchanges = [
            ccxt.bybit()
        ]

        # Fetch all available symbols from ByBit
        symbols = ccxt.bybit().fetch_tickers().keys()

        # Filter only the symbols that end with /USDT
        symbols = [symbol for symbol in symbols if symbol.endswith('/USDT')]

        # Create a new session
        session = Session()

        # For each symbol
        for symbol in symbols:
            ohlcv = None
            # Fetch OHLCV data from the first exchange that supports the market
            for exchange in exchanges:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, '15m')
                    break
                except ccxt.BaseError:
                    continue

            if ohlcv is None:
                print(f"Failed to fetch OHLCV data for symbol {symbol}")
                continue

            # For each OHLCV data point
            for data in ohlcv:
                timestamp, open, high, low, close, volume = data

                # Convert timestamp to datetime
                timestamp = datetime.fromtimestamp(timestamp / 1000)

                # Check if a row with the same timestamp already exists
                existing_ohlcv = session.query(OHLCV).filter_by(symbol=symbol, timeframe='15m', timestamp=timestamp).first()

                if existing_ohlcv is None:
                    # Create a new OHLCV object
                    ohlcv_data = OHLCV(
                        symbol=symbol,
                        timeframe='15m',
                        timestamp=timestamp,
                        open=Decimal(open),
                        high=Decimal(high),
                        low=Decimal(low),
                        close=Decimal(close),
                        volume=Decimal(volume)
                    )

                    # Add the OHLCV data to the session
                    session.add(ohlcv_data)

            # Commit the session to save the data
            session.commit()

            # Calculate indicators
            df = calculate_indicators(symbol)

        # Close the session
        session.close()

    if __name__ == "__main__":
        while True:
            fetch_ohlcv_data(None)
            time.sleep(15 * 60)  # Sleep for 15 minutes
