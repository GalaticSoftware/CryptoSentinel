# This script is used to detect signals in the data and return a list of signals

# Import the libraries
import psycopg2
from psycopg2 import sql
import pandas as pd
from pandas import DataFrame, Series, Timestamp, Timedelta, to_datetime, isnull, notnull, merge
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import MY_POSTGRESQL_URL
from data_processing.data_processor import process_ohlcv

# Connect to the PostgreSQL database
conn = psycopg2.connect(MY_POSTGRESQL_URL)
cur = conn.cursor()

# Define the signal detector
def detect_signals(symbol, timeframe):
    # Create a SQL query to fetch the OHLCV data from the database
    query = sql.SQL(
        "SELECT * FROM ohlcv "
        "WHERE symbol = %s AND timestamp = %s "
        "ORDER BY timestamp ASC"
    )
    # Execute the query
    cur.execute(query, (symbol, timeframe))
    # Fetch the results
    results = cur.fetchall()

    # Convert the OHLCV data to a Pandas DataFrame
    df = pd.DataFrame(results, columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])

    # Process the OHLCV data
    processed_values = df[["open", "high", "low", "close", "volume"]].apply(process_ohlcv, axis=1)
    df[["processed_ohlcv_1", "processed_ohlcv_2", "processed_ohlcv_3"]] = pd.DataFrame(processed_values.tolist())




    # Calculate the EMA
    df["ema"] = df["close"].ewm(span=20, adjust=False).mean()

    # Calculate the MACD
    df["macd"] = df["close"].ewm(span=12, adjust=False).mean() - df["close"].ewm(span=26, adjust=False).mean()

    # Calculate the signal line
    df["signal_line"] = df["macd"].ewm(span=9, adjust=False).mean()

    # Calculate the MACD histogram
    df["macd_histogram"] = df["macd"] - df["signal_line"]

    # Calculate the RSI
    df["change"] = df["close"].diff()
    df["gain"] = df["change"].apply(lambda x: x if x > 0 else 0)
    df["loss"] = df["change"].apply(lambda x: abs(x) if x < 0 else 0)
    df["avg_gain"] = df["gain"].ewm(span=14, adjust=False).mean()
    df["avg_loss"] = df["loss"].ewm(span=14, adjust=False).mean()
    df["rs"] = df["avg_gain"] / df["avg_loss"]
    df["rsi"] = 100 - (100 / (1 + df["rs"]))
    df = df.drop(columns=["change", "gain", "loss", "avg_gain", "avg_loss", "rs"])

    # Calculate the Bollinger Bands
    df["std"] = df["close"].rolling(window=20).std()
    df["upper_band"] = df["ema"] + (df["std"] * 2)
    df["lower_band"] = df["ema"] - (df["std"] * 2)
    df = df.drop(columns=["std"])
    
    # Calculate the Stochastic Oscillator
    df["l14"] = df["low"].rolling(window=14).min()
    df["h14"] = df["high"].rolling(window=14).max()
    df["k"] = ((df["close"] - df["l14"]) / (df["h14"] - df["l14"])) * 100
    df["d"] = df["k"].rolling(window=3).mean()
    df = df.drop(columns=["l14", "h14"])

    # Calculate the Williams %R
    df["r"] = ((df["h14"] - df["close"]) / (df["h14"] - df["l14"])) * -100



    # Create a list of signals
    signals = []

    # Check for signals
    for i in range(1, len(df)):
        # Check for MACD crossover and other conditions
        # (Add your signal detection logic here)
        signals.append("signal")

    # Add the signals to the DataFrame
    df["signal"] = signals

    # Print the signals to the console
    print(df[["timestamp", "close", "signal"]])

# Define the main function
def main():
    # Define the symbol and timeframe
    symbol = "BTC/USDT"
    timeframe = 1685023200000  # Provide the correct timeframe value

    # Detect signals
    detect_signals(symbol, timeframe)

# Execute the main function
if __name__ == "__main__":
    main()