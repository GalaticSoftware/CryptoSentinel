import requests
import logging
import ccxt
import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import ta
import os
from datetime import datetime, timedelta


from telegram import Update
from telegram.ext import CallbackContext
from bot.utils import restricted
from config.settings import LUNARCRUSH_API_KEY


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CotdHandler:
    @staticmethod
    def plot_ohlcv_chart(symbol):
        # Fetch OHLCV data from Binance
        exchange = ccxt.bybit()
        ohlcv = exchange.fetch_ohlcv(symbol.upper()+'/USDT', '4h')
        
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
        fig.write_image(f"charts/{symbol}_chart.png", scale=1.5, width=1000, height=600)

    @staticmethod
    def coin_of_the_day(update: Update, context: CallbackContext):
        # Fetch Coin of the Day data from LunarCrush API
        url = "https://lunarcrush.com/api3/coinoftheday"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.exception("Connection error while fetching Coin of the Day from LunarCrush API")
            update.message.reply_text("Error connecting to LunarCrush API. Please try again later.")
            return

        if "name" in data and "symbol" in data:
            coin_name = data["name"]
            coin_symbol = data["symbol"]

            # Fetch and plot the OHLCV chart
            try:
                CotdHandler.plot_ohlcv_chart(coin_symbol)
            except Exception as e:
                logger.exception("Error while plotting the OHLCV chart")
                update.message.reply_text("Error while plotting the OHLCV chart. Please try again later.")
                return

            # Send the chart and the Coin of the Day message
            image_path = f"charts/{coin_symbol}_chart.png"
            try:
                with open(image_path, "rb") as f:
                    context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
                update.message.reply_text(f"Coin of the Day: {coin_name} ({coin_symbol})")
                
                # Delete the image file after sending it
                os.remove(image_path)
            except Exception as e:
                logger.exception("Error while sending the chart and the Coin of the Day message")
                update.message.reply_text("Error while sending the chart and the Coin of the Day message. Please try again later.")
                return
            
        else:
            logger.error("Error in LunarCrush API response: Required data not found")
            update.message.reply_text("Error fetching Coin of the Day data. Please try again later.")




