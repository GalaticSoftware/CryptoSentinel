import pandas as pd
from ta.volume import OnBalanceVolumeIndicator, AccDistIndexIndicator
from ta.volume import MFIIndicator
from ta.utils import dropna
from bot.database import OHLCV, Session
import time
import ccxt

# Fetch all available symbols from ByBit
symbols = ccxt.bybit().fetch_tickers().keys()

def calculate_indicators(symbol):
    # Create a new session
    session = Session()

    # Query the OHLCV data
    ohlcv_data = session.query(OHLCV).filter_by(symbol=symbol, timeframe='15m').order_by(OHLCV.timestamp).all()

    # Create a DataFrame from the OHLCV data
    df = pd.DataFrame([{
        'date': data.timestamp,
        'high': float(data.high),
        'low': float(data.low),
        'close': float(data.close),
        'volume': float(data.volume)
    } for data in ohlcv_data])

    # Clean NaN values
    df = dropna(df)

    # Calculate Money Flow Index (MFI)
    mfi = MFIIndicator(df['high'], df['low'], df['close'], df['volume'], fillna=True)
    df['mfi'] = mfi.money_flow_index()

    # On-Balance Volume (OBV)
    obv_indicator = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume'])
    df['obv'] = obv_indicator.on_balance_volume()

    # Calculate Accumulation/Distribution Index (ADI)
    adi_indicator = AccDistIndexIndicator(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
    df['adi'] = adi_indicator.acc_dist_index()

    # Generate signals based on the indicators
    df['mfi_signal'] = df['mfi'].apply(lambda x: 'overbought' if x > 80 else 'oversold' if x < 20 else 'neutral')
    df['obv_signal'] = df['obv'].diff().apply(lambda x: 'buy' if x > 0 else 'sell' if x < 0 else 'neutral')
    df['adi_signal'] = df['adi'].diff().apply(lambda x: 'buy' if x > 0 else 'sell' if x < 0 else 'neutral')

    # Close the session
    session.close()

    # Return the DataFrame
    return df

if __name__ == "__main__":
    while True:
        # Calculate indicators for each symbol
        for symbol in symbols:
            calculate_indicators(symbol)
        time.sleep(15 * 60)  # Sleep for 15 minutes
