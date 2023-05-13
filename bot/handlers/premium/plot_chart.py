import logging
import ccxt
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import ta
import os
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext
from bot.utils import log_command_usage
from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartHandler:
    @staticmethod
    def plot_ohlcv_chart(symbol):
        # Fetch OHLCV data from Binance
        exchange = ccxt.bybit()
        ohlcv = exchange.fetch_ohlcv(symbol.upper(), '4h')

        # Filter data to display only the last 4 weeks
        two_weeks_ago = datetime.now() - timedelta(weeks=4)
        ohlcv = [entry for entry in ohlcv if datetime.fromtimestamp(entry[0] // 1000) >= two_weeks_ago]

        # Convert timestamp to datetime objects
        for entry in ohlcv:
            entry[0] = datetime.fromtimestamp(entry[0] // 1000)

        # Create a DataFrame and set 'Date' as the index
        df = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df.set_index('Date', inplace=True)

        # Add RSI
        delta = df['Close'].diff()
        gain, loss = delta.where(delta > 0, 0), delta.where(delta < 0, 0).abs()
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        df['RSI'] = rsi

        # Add moving averages
        df['SMA21'] = ta.trend.sma_indicator(df['Close'], window=21)
        df['SMA50'] = ta.trend.sma_indicator(df['Close'], window=50)

        # Create a Plotly figure
        fig = go.Figure()

        # Add OHLCV data
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))

        # Add moving averages
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA21'], mode='lines', name='SMA21', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='SMA50', line=dict(color='blue', width=1)))

        # Customize the layout
        fig.update_layout(
            title=f'{symbol} OHLCV Chart',
            xaxis=dict(type='date', tickformat="%H:%M %b-%d", tickmode='auto', nticks=10, rangeslider=dict(visible=False)),
            yaxis=dict(title='Price (USDT)'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            template='plotly_dark',
            margin=dict(b=40, t=40, r=40, l=40)
        )

        # Save the chart as a PNG image
        chart_file = f"charts/{symbol}_chart.png"
        fig.write_image(chart_file, scale=1.5, width=1000, height=600)

        return chart_file

    @staticmethod
    @restricted
    @log_command_usage
    def plot_chart(update: Update, context: CallbackContext):
        # Get the user's input
        symbol = context.args[0]  # Assuming the symbol is passed as a command argument

        try:
            chart_file = ChartHandler.plot_ohlcv_chart(symbol)
        except Exception as e:
            logger.exception("Error while plotting the OHLCV chart")
            update.message.reply_text("Error while plotting the OHLCV chart. Please try again later.")
            return

        # Send the chart
        try:
            with open(chart_file, "rb") as f:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
        except Exception as e:
            logger.exception("Error while sending the chart")
            update.message.reply_text("Error while sending the chart. Please try again later.")
            return

        # Delete the image file after sending it
        os.remove(chart_file) 
