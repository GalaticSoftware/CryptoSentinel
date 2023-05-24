import pandas as pd
import time
from telegram.ext import CallbackContext
import telegram
from bot.database import User, Session
from data_analyzer_module.market.scanner import calculate_indicators

# setup logging
import logging
logger = logging.getLogger(__name__)

import ccxt
from bot.utils import PlotChart

# Initialize ByBit exchange
bybit = ccxt.bybit()

# Fetch all available symbols from ByBit
symbols = bybit.fetch_tickers().keys()

class IndicatorAlerts:
    def check_indicator_alerts(context: CallbackContext):
        # Create a new session
        session = Session()

        # Query all users
        users = session.query(User).all()

        # For each symbol
        for symbol in symbols:
            df = calculate_indicators(symbol)
            if df.empty:  # Check if DataFrame is empty
                print(f"No data available for symbol: {symbol}")
                continue
            latest_signals = df.iloc[-1]

            # Plot the chart for the symbol with the indicators
            chart_file = PlotChart.plot_ohlcv_chart(symbol, '1d')  # assuming '1d' as the timeframe

            # For each user
            for user in users:
                # Generate an alert message based on the latest signals
                alert_message = f"🔔 Indicator Alert for {symbol}! 🔔\n\n"
                alert_message += f"MFI: {latest_signals['mfi_signal']}\n"
                alert_message += f"OBV: {latest_signals['obv_signal']}\n"
                alert_message += f"ADI: {latest_signals['adi_signal']}\n"

                try:
                    # Send the alert message to the user
                    context.bot.send_message(chat_id=user.telegram_id, text=alert_message)

                    # Send the chart to the user
                    context.bot.send_photo(chat_id=user.telegram_id, photo=open(chart_file, 'rb'))
                except telegram.error.BadRequest as e:
                    logger.error(f"Failed to send message to chat_id={user.telegram_id}: {e}")

        # Close the session
        session.close()



    if __name__ == "__main__":
        while True:
            check_indicator_alerts()
            time.sleep(15 * 60)  # Sleep for 15 minutes
