# data_collection/data_collector.py

import ccxt
import psycopg2
from psycopg2 import sql

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MY_POSTGRESQL_URL

# Initialize the Binance client
exchange = ccxt.binance()

# Connect to the PostgreSQL database
conn = psycopg2.connect(MY_POSTGRESQL_URL)
cur = conn.cursor()

def get_ohlcv(symbol, timeframe):
    data = exchange.fetch_ohlcv(symbol, timeframe)
    return data[-1]  # Return the latest OHLCV data

def store_ohlcv(symbol, ohlcv):
    # Create a SQL query
    query = sql.SQL(
        "INSERT INTO ohlcv (symbol, timestamp, open, high, low, close, volume) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT (symbol, timestamp) DO UPDATE "
        "SET open = %s, high = %s, low = %s, close = %s, volume = %s"
    )

    # Execute the query
    cur.execute(query, (symbol, *ohlcv, *ohlcv[1:]))

    # Commit the transaction
    conn.commit()

if __name__ == "__main__":
    symbol = "BTC/USDT"
    timeframe = "1h"  # Fetch hourly OHLCV data
    ohlcv = get_ohlcv(symbol, timeframe)
    store_ohlcv(symbol, ohlcv)
    print(f"The latest OHLCV data for {symbol} is {ohlcv}")
