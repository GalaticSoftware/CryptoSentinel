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
from bot.utils import log_command_usage, restricted, command_usage_example
from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted
from bot.utils import PlotChart

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChartHandler:
    @staticmethod
    @restricted
    @log_command_usage("chart")
    @command_usage_example(
        "/chart BTCUSDT 4h - Defaults to 4hr chart if time frame is not provided"
    )
    def plot_chart(update: Update, context: CallbackContext):
        # Get the user's input
        symbol = context.args[0]  # symbol is passed as a command argument
        time_frame = (
            context.args[1] if len(context.args) > 1 else "4h"
        )  # Set default to 4h if not provided

        try:
            chart_file = PlotChart.plot_ohlcv_chart(symbol, time_frame)
        except Exception as e:
            logger.exception("Error while plotting the OHLCV chart")
            update.message.reply_text(
                "Error while plotting the OHLCV chart. Please try again later."
            )
            return

        # Send the chart
        try:
            with open(chart_file, "rb") as f:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
        except Exception as e:
            logger.exception("Error while sending the chart")
            update.message.reply_text(
                "Error while sending the chart. Please try again later."
            )
            return

        # Delete the image file after sending it
        os.remove(chart_file)
