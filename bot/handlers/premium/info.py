import logging
import ccxt
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import ta
import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext
from bot.utils import log_command_usage
from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted, PlotChart

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfoHandler:
    SYMBOL_MAPPING = {
        "BTC": 1,
        "ETH": 2,
        # Add more mappings as needed
    }

    @staticmethod
    def get_coin_info(symbol):
        if symbol in InfoHandler.SYMBOL_MAPPING:
            coin_id = InfoHandler.SYMBOL_MAPPING[symbol]
        else:
            logger.error("Symbol mapping not found")
            return None

        url = f"https://lunarcrush.com/api3/coins/{coin_id}"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.exception("Connection error while fetching coin info from LunarCrush API")
            return None

        if "data" in data:
            coin_data = data["data"]
            return coin_data
        else:
            logger.error("Error in LunarCrush API response: Required data not found")
            return None

    @staticmethod
    @restricted
    @log_command_usage
    def get_coin_info_command(update: Update, context: CallbackContext):
        # Get the user's input
        symbol = context.args[0]  # Assuming the symbol is passed as a command argument

        # Fetch coin info
        coin_data = InfoHandler.get_coin_info(symbol)
        if coin_data is None:
            update.message.reply_text("Error fetching coin info. Please try again later.")
            return

        # Extract relevant information
        name = coin_data.get("name")
        symbol = coin_data.get("symbol")
        price = coin_data.get("price")
        percent_change_24h = coin_data.get("percent_change_24h")
        percent_change_7d = coin_data.get("percent_change_7d")
        percent_chagne_30d = coin_data.get("percent_change_30d")
        market_cap = coin_data.get("market_cap")
        sentiment_relative = coin_data.get("sentiment_relative")

        # Generate the response message
        message = (
        f"""Coin Info:\n
        🪙 Symbol: {symbol}
        📛 Name: {name}
        💰 Price: {price}
        📈 24h % Change: {percent_change_24h}
        📊 7d % Change: {percent_change_7d}
        📊 30d % Change: {percent_chagne_30d}
        💼 Market Cap: {market_cap}
        🐮 Bullish Twitter Sentiment %: {sentiment_relative}"""
        )

        # Plot chart
        chart_file = PlotChart.plot_ohlcv_chart(symbol)

        # Send chart and info as a reply
        update.message.reply_photo(open(chart_file, 'rb'), caption=message)

