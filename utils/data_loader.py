import ccxt
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self):
        self.exchange = None

    def initialize_exchange(self, exchange_name):
        try:
            self.exchange = getattr(ccxt, exchange_name)()
            self.exchange.load_markets()
        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            return False
        return True

    def check_symbol(self, symbol):
        return symbol in self.exchange.symbols

    def fetch_ohlcv(self, symbol, timeframe, since=1262304000000):
        ohlcv = []
        while True:
            try:
                new_data = self.exchange.fetch_ohlcv(symbol, timeframe, since)
                if len(new_data) == 0:
                    break
                ohlcv += new_data
                since = new_data[-1][0] + 1  # +1 to avoid duplicates
            except Exception as e:
                logger.error(f"Failed to fetch ohlcv: {e}")
                break
        return ohlcv

    def convert_timestamp(self, ohlcv):
        df = pd.DataFrame(
            ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df


# Example usage
# if __name__ == "__main__":
#    loader = DataLoader()
#    if loader.initialize_exchange("binance"):
#        symbol = "BTC/USDT"
#        timeframe = "1d"
#        if loader.check_symbol(symbol):
#            ohlcv = loader.fetch_ohlcv(symbol, timeframe)
#            if ohlcv:
#                loader.save_to_csv(ohlcv, symbol, timeframe)
