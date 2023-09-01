import logging
import requests
import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.utils import log_command_usage, restricted, PlotChart, command_usage_example
from config.settings import LUNARCRUSH_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfoHandler:
    SYMBOL_MAPPING = {
        "BTC": 1,
        "ETH": 2,
        "XRP": 3,
        "LTC": 4,
        "BCH": 5,
        "BNB": 6,
        "USDT": 7,
        "EOS": 8,
        "BSV": 9,
        "XLM": 10,
        "ADA": 11,
        "TRX": 12,
        "XMR": 13,
        "LEO": 14,
        "DASH": 15,
        "NEO": 16,
        "IOTA": 17,
        "LINK": 18,
        "ATOM": 19,
        "XTZ": 20,
    }

    @staticmethod
    def get_coin_info(symbol):
        # Check if symbol exists in mapping
        if symbol in InfoHandler.SYMBOL_MAPPING:
            coin_id = InfoHandler.SYMBOL_MAPPING[symbol]
        else:
            logger.error("Symbol mapping not found")
            return None

        # Prepare API request
        url = f"https://lunarcrush.com/api3/coins/{coin_id}"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.exception(
                "Connection error while fetching coin info from LunarCrush API")
            return None

        # Check if data exists in the response
        if "data" in data:
            coin_data = data["data"]
            return coin_data
        else:
            logger.error(
                "Error in LunarCrush API response: Required data not found")
            return None

    @staticmethod
    @restricted
    @log_command_usage("info")
    @command_usage_example("/info BTCUSDT 1d - Defaults to 4h if no time frame is provided")
    def get_coin_info_command(update: Update, context: CallbackContext):
        # Get the user's input
        # Assuming the symbol is passed as a command argument
        input_arg = context.args[0]

        # Split the input_arg into cryptocurrency symbol and currency symbol
        # Get the cryptocurrency symbol (e.g., "BTC" from "BTCUSDT")
        symbol = input_arg[:-4]
        # Get the currency symbol (e.g., "USDT" from "BTCUSDT")
        currency = input_arg[-4:]

        # Set default time frame
        time_frame = '4h'

        # Check if a custom time frame is provided
        if len(context.args) > 1:
            time_frame = context.args[1]

        # Fetch coin info
        coin_data = InfoHandler.get_coin_info(symbol)
        if coin_data is None:
            update.message.reply_text(
                "Error fetching coin info. Please try again later.")
            return

        # Extract relevant information
        name = coin_data.get("name")
        symbol = coin_data.get("symbol")
        # get price and format it to 2 decimal places
        price = "{:.2f}".format(coin_data.get("price"))
        percent_change_24h = coin_data.get("percent_change_24h")
        percent_change_7d = coin_data.get("percent_change_7d")
        percent_chagne_30d = coin_data.get("percent_change_30d")

        # Generate the response message
        message = (
            f"Coin Info:\n"
            f"🪙 Symbol: {symbol}\n"
            f"📛 Name: {name}\n"
            f"💰 Price: {price} {currency}\n"
            f"📈 {percent_change_24h}% (Change in 24 hours)\n"
            f"📊 {percent_change_7d}% (Change in 7 days)\n"
            f"📊 {percent_chagne_30d}% (Change in 30 days)"
        )

        # Plot chart with specified time frame
        chart_file = PlotChart.plot_ohlcv_chart(symbol, time_frame)

        # Send chart and info as a reply
        update.message.reply_photo(open(chart_file, 'rb'), caption=message)

        # Delete the image file after sending it
        os.remove(chart_file)
