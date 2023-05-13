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
from bot.utils import PlotChart

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartHandler:
    @staticmethod
    @restricted
    @log_command_usage
    def plot_chart(update: Update, context: CallbackContext):
        # Get the user's input
        symbol = context.args[0]  # Assuming the symbol is passed as a command argument

        try:
            chart_file = PlotChart.plot_ohlcv_chart(symbol)
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
