from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from users.management import check_user_access
import ccxt
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import ta
import os
from datetime import datetime, timedelta
import requests
from config.settings import LUNARCRUSH_API_KEY
import asyncio
import aiohttp
import ccxt
import pandas as pd
import plotly.graph_objects as go
import ta


import functools
from bot.database import Session, CommandUsage

def restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id == 1:  # bypass restriction for test user
            return func(update, context, *args, **kwargs)
        if not check_user_access(user_id):
            update.message.reply_text(
                "You don't have access to this feature. Please subscribe first by using /start."
            )
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def log_command_usage(command_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the user ID
            update = args[-2]
            context = args[-1]
            user_id = update.effective_user.id

            # Log command usage to the database
            session = Session()
            command_usage = session.query(CommandUsage).filter_by(user_id=user_id, command_name=command_name).first()

            if command_usage:
                command_usage.usage_count += 1  # Increment the counter if the command usage record exists
            else:
                command_usage = CommandUsage(user_id=user_id, command_name=command_name, usage_count=1)
                session.add(command_usage)

            session.commit()

            # Call the original command handler function
            return func(*args, **kwargs)

        return wrapper
    return decorator






def command_usage_example(example_text: str):
    def decorator(function):
        def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
            if len(context.args) == 0:
                update.message.reply_text(f"Usage example: {example_text}")
                return
            return function(update, context, *args, **kwargs)
        return wrapper
    return decorator


class PlotChart:
    @staticmethod
    async def fetch_ohlcv(exchange, symbol, time_frame):
        try:
            return await exchange.fetch_ohlcv(symbol, time_frame)
        except ccxt.BaseError:
            return None

    @staticmethod
    def add_indicators(df):
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

    @staticmethod
    def generate_chart(df, symbol, time_frame):
        # Create a Plotly figure
        fig = go.Figure()

        # Add OHLCV data
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'))

        # Add moving averages
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA21'], mode='lines', name='SMA21', line=dict(color='orange', width=1)))
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', name='SMA50', line=dict(color='blue', width=1)))

        # Customize the layout
        fig.update_layout(
            title=f'{symbol} OHLCV Chart ({time_frame})',
            xaxis=dict(type='date', tickformat="%H:%M %b-%d", tickmode='auto', nticks=10, rangeslider=dict(visible=False)),
            yaxis=dict(title='Price (USDT)'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            template='plotly_dark',
            margin=dict(b=40, t=40, r=40, l=40)
        )

        # Save the chart as a PNG image
        chart_file = f"charts/{symbol}_chart_{time_frame}.png"
        fig.write_image(chart_file, scale=1.5, width=1000, height=600)

        return chart_file

    @staticmethod
    async def plot_ohlcv_chart(symbol, time_frame):
        # Define the list of exchanges
        exchanges = [
            ccxt.binance(),
            ccxt.bybit(),
            ccxt.kucoin(),
        ]

        async with aiohttp.ClientSession() as session:
            tasks = []
            for exchange in exchanges:
                task = asyncio.ensure_future(
                    PlotChart.fetch_ohlcv(exchange, symbol.upper() + '/USDT', time_frame)
                )
                tasks.append(task)

            ohlcv_results = await asyncio.gather(*tasks)

        # Filter out None values and select the first OHLCV data
        ohlcv = next((data for data in ohlcv_results if data is not None), None)

        if ohlcv is None:
            return None  # Return None if no exchange supports the market

        # Create a DataFrame and set 'Date' as the index
        df = pd.DataFrame(ohlcv, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Date'] = pd.to_datetime(df['Date'], unit='ms')
        df.set_index('Date', inplace=True)

        # Filter data based on the selected time frame
        time_horizon = {
            '1m': '12H',
            '5m': '1D',
            '15m': '3D',
            '1h': '7D',
            '4h': '2W',
            '1d': '12W',
            '1w': '80W',
            '1M': '324W',
        }
        start_time = pd.Timestamp.now() - pd.Timedelta(time_horizon.get(time_frame, '4W'))
        df = df[df.index >= start_time]

        # Add indicators
        PlotChart.add_indicators(df)

        # Generate the chart
        return PlotChart.generate_chart(df, symbol, time_frame)