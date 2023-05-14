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


def log_command_usage(func):
    @functools.wraps(func)
    def wrapper(update, context, *args, **kwargs):
        # Get the command name and user ID
        command_name = func.__name__
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
        return func(update, context, *args, **kwargs)

    return wrapper



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
    def plot_ohlcv_chart(symbol, time_frame):
        # Fetch OHLCV data from Binance
        exchange = ccxt.bybit()
        ohlcv = exchange.fetch_ohlcv(symbol.upper() + '/USDT', time_frame)

        # Define the time horizon for each time frame
        time_horizon = {
            '1m': timedelta(days=1),
            '5m': timedelta(days=3),
            '15m': timedelta(days=7),
            '1h': timedelta(days=14),
            '4h': timedelta(weeks=4),
            '1d': timedelta(weeks=12),
            '1w': timedelta(weeks=80),
            '1M': timedelta(weeks=324),
        }

        # Filter data based on the selected time frame
        start_time = datetime.now() - time_horizon.get(time_frame, timedelta(weeks=4))
        ohlcv = [entry for entry in ohlcv if datetime.fromtimestamp(entry[0] // 1000) >= start_time]

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





