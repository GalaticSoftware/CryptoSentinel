import logging
import requests
import os
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import ta
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from bot.utils import restricted, log_command_usage, PlotChart, command_usage_example
from config.settings import X_RAPIDAPI_KEY
from cachetools import cached, TTLCache


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize cache with a TTL of 4 hours
cache = TTLCache(maxsize=100, ttl=14400)


class StatsHandler:
    @staticmethod
    @cached(cache)
    def fetch_data(symbol: str, endpoint: str, timeframe: str):
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/{endpoint}/{symbol}/{timeframe}"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        return response.json()

    @staticmethod
    def filter_patterns(data: dict):
        return {
            k: v
            for k, v in data.items()
            if v is True and k not in ["timestamp", "symbol", "timeframe", "prices"]
        }

    @staticmethod
    def generate_patterns_message(symbol: str, patterns: dict):
        return f"Patterns for {symbol}:\n\n" + "\n".join(patterns.keys())

    @staticmethod
    def send_patterns_message(update: Update, patterns_message: str):
        update.message.reply_text(patterns_message)
        logger.info("Patterns message sent")

    @staticmethod
    def fetch_rsi_data(symbol: str, indicator: str, timeframe: str):
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/{indicator}/{symbol}/{timeframe}/14"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data

    @staticmethod
    def fetch_obv_data(symbol: str, indicator: str, timeframe: str):
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/{indicator}/{symbol}/{timeframe}/4"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data

    @staticmethod
    def fetch_mfi_data(symbol: str, indicator: str, timeframe: str):
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/{indicator}/{symbol}/{timeframe}/14"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data

    @staticmethod
    def fetch_macd_data(symbol: str, indicator: str, timeframe: str):
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/{indicator}/{symbol}/{timeframe}/5/8/3"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        return data

    @staticmethod
    @restricted
    @log_command_usage("stats")
    @command_usage_example("/stats BTCUSDT 1d")
    def stats(update: Update, context: CallbackContext):
        logger.info("Stats command received")
        if len(context.args) < 2:
            update.message.reply_text("Please provide both symbol and timeframe.")
            return

        symbol = context.args[0]
        timeframe = context.args[1]

        # Send a Loading message and tag it so we can delete it later
        loading_message = update.message.reply_text(
            "Loading Data... Please wait.", quote=True
        )

        # Fetch pattern data
        pattern_data = StatsHandler.fetch_data(symbol, "patterns", timeframe)
        patterns = StatsHandler.filter_patterns(pattern_data)
        patterns_message = StatsHandler.generate_patterns_message(symbol, patterns)

        # Send patterns message
        StatsHandler.send_patterns_message(update, patterns_message)

        # Fetch RSI data
        rsi_data = StatsHandler.fetch_rsi_data(symbol, "rsi", timeframe)

        # RSI overbought/oversold
        if "rsi" in rsi_data and rsi_data["rsi"]:
            latest_rsi = rsi_data["rsi"][-1]
            if latest_rsi > 70:
                rsi_status = "RSI overbought"
            elif latest_rsi < 30:
                rsi_status = "RSI oversold"
            else:
                rsi_status = "RSI is in normal range"
            update.message.reply_text(f"Latest RSI: {latest_rsi}. {rsi_status}")
        else:
            logger.error("RSI data not found in API response")
            update.message.reply_text(
                "Unable to check RSI overbought/oversold status due to missing data"
            )

        logger.info("RSI overbought/oversold checked")

        # Fetch OBV data
        obv_data = StatsHandler.fetch_obv_data(symbol, "obv", timeframe)

        if "obv" in obv_data and obv_data["obv"]:
            latest_obv = obv_data["obv"][-1]
            previous_obv = obv_data["obv"][-2]
            if latest_obv > previous_obv:
                obv_status = "OBV is rising"
            elif latest_obv < previous_obv:
                obv_status = "OBV is falling"
            else:
                obv_status = "OBV is flat"
            update.message.reply_text(f"Latest OBV: {latest_obv}. {obv_status}")

        # Fetch MFI data
        mfi_data = StatsHandler.fetch_mfi_data(symbol, "mfi", timeframe)

        if "mfi" in mfi_data and mfi_data["mfi"]:
            latest_mfi = mfi_data["mfi"][-1]
            if latest_mfi > 80:
                mfi_status = "MFI overbought"
            elif latest_mfi < 20:
                mfi_status = "MFI oversold"
            else:
                mfi_status = "MFI is in normal range"
            update.message.reply_text(f"Latest MFI: {latest_mfi}. {mfi_status}")

        # Fetch MACD data
        macd_data = StatsHandler.fetch_macd_data(symbol, "macd", timeframe)

        # define 2 dictionaries to store the last 2 periods of MACD data
        latest_macd = {}
        previous_macd = {}

        # filter and store the last 2 periods of MACD data
        if "macd" in macd_data and macd_data["macd"]:
            latest_macd = macd_data["macd"][-1]
            previous_macd = macd_data["macd"][-2]

        # check if the histogram is rising or falling
        if (
            "histogram" in latest_macd
            and "histogram" in previous_macd
            and latest_macd["histogram"] > previous_macd["histogram"]
        ):
            macd_status = "MACD histogram is rising"
        elif (
            "histogram" in latest_macd
            and "histogram" in previous_macd
            and latest_macd["histogram"] < previous_macd["histogram"]
        ):
            macd_status = "MACD histogram is falling"
        else:
            macd_status = "MACD histogram is flat"

        # send MACD status to user
        update.message.reply_text(f"{macd_status}")

        # Update the loading message to indicate that the chart is being generated
        loading_message.edit_text("Generating chart...")
        # Plot chart
        chart_file = PlotChart.plot_ohlcv_chart(symbol, timeframe)

        # Update the loading message to indicate that the chart has been generated
        loading_message.edit_text("Sending chart...")

        # Send chart to user and then delete it
        if chart_file:
            with open(chart_file, "rb") as f:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
            os.remove(chart_file)

        # Delete the loading message
        loading_message.delete()
        logger.info("Stats command completed")

    @staticmethod
    def command_handler() -> CommandHandler:
        return CommandHandler("stats", StatsHandler.stats, pass_args=True)
