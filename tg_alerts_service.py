import pika
import json
import logging
import pandas as pd

from utils import DataLoader  # Assuming DataLoader is in a file called utils.py
from config.settings import CLOUDAMQP_URL


class CryptoScanner:
    def __init__(self):
        self.loader = DataLoader()
        self.params = pika.URLParameters(CLOUDAMQP_URL)
        self.connection = pika.BlockingConnection(self.params)
        self.channel = self.connection.channel()

    def calculate_rvol(self, ohlcv_data):
        df = pd.DataFrame(ohlcv_data, columns=[
                          'timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        # Average volume over the past 30 days
        avg_volume = df['Volume'].tail(30).mean()
        today_volume = df['Volume'].iloc[-1]  # Today's volume
        rvol = today_volume / avg_volume  # Calculate RVol
        return rvol

    def scan_symbol(self, symbol):
        ohlcv_data = self.loader.fetch_ohlcv(symbol, '1d')  # 1-day timeframe
        rvol = self.calculate_rvol(ohlcv_data)
        if rvol > 1.5:
            alert_message = {"type": "RVol Alert",
                             "symbol": symbol, "RVol": rvol}
            self.channel.basic_publish(
                exchange='', routing_key='telegram', body=json.dumps(alert_message))
            print(f"RVol Alert for {symbol}: {rvol}")

    def scan(self):
        if not self.loader.initialize_exchange("bybit"):
            return
        symbols = self.loader.exchange.symbols
        for symbol in symbols:
            self.scan_symbol(symbol)
        self.connection.close()


if __name__ == '__main__':
    scanner = CryptoScanner()
    scanner.scan()
