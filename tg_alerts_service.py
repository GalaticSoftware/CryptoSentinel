import pika
import json
import logging
import pandas as pd
import uuid

from utils import DataLoader
from config.settings import CLOUDAMQP_URL

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CryptoScanner:
    def __init__(self):
        self.loader = DataLoader()
        self.params = pika.URLParameters(CLOUDAMQP_URL)
        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()

    def calculate_rvol(self, ohlcv_data):
        df = pd.DataFrame(ohlcv_data, columns=[
                          'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        rvol = None  # Initialize rvol to None

        if not df.empty and 'Volume' in df.columns:
            today_volume = df['Volume'].iloc[-1]  # Today's volume

            # Average volume over the past 30 days
            avg_volume = df['Volume'].tail(30).mean()
            rvol = today_volume / avg_volume  # Calculate RVol
        else:
            print('Either the dataframe is empty or the Volume column is missing')
        return rvol  # Return rvol, which will be None if not calculated

    def scan_symbol(self, symbol):
        ohlcv_data = self.loader.fetch_ohlcv(symbol, '1d')  # 1-day timeframe
        rvol = self.calculate_rvol(ohlcv_data)
        if rvol and rvol > 1.5:  # Check if rvol is not None and greater than 1.5
            update_id = str(uuid.uuid4())  # Generate a unique identifier
            alert_message = {
                "type": "RVol Alert",
                "symbol": symbol,
                "RVol": rvol,
                "update_id": update_id  # Include the update_id in the message
            }
            self.channel.basic_publish(
                exchange='', routing_key='telegram', body=json.dumps(alert_message))
            print(f"RVol Alert for {symbol}: {rvol}")

    def scan(self):
        self.loader.initialize_exchange('bybit')
        symbols = self.loader.exchange.symbols
        for symbol in symbols:
            self.scan_symbol(symbol)


if __name__ == '__main__':
    scanner = CryptoScanner()
    logger.info('Starting CryptoScanner')
    scanner.scan()
