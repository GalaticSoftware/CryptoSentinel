import logging
import requests
import os
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from bot.utils import restricted, log_command_usage, PlotChart
from config.settings import X_RAPIDAPI_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class StatsHandler:
    @staticmethod
    def stats(update: Update, context: CallbackContext):
        logger.info("Stats command received")
        symbol = context.args[0] if context.args else "BTCUSDT"
        url = f"https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/patterns/{symbol}/4h"
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "cryptocurrencies-technical-study.p.rapidapi.com",
        }

        # Send a loading message
        message = update.message.reply_text("Fetching data...")

        response = requests.get(url, headers=headers)
        data = response.json()
        logger.info(data)

        # Filter out patterns that are not present
        patterns = {
            k: v
            for k, v in data.items()
            if v is True and k not in ["timestamp", "symbol", "timeframe", "prices"]
        }
        logger.info(patterns)

        # Generate a message with the present patterns
        patterns_message = f"Patterns for {symbol}:\n\n" + "\n".join(patterns.keys())
        logger.info(patterns_message)

        # Update the loading message to indicate that the data has been fetched
        message.edit_text("Data fetched. Generating chart...")
        logger.info("Loading message updated")

        # Send the message
        update.message.reply_text(patterns_message)
        logger.info("Stats command completed")

        # Fetch technical indicator data
        # TODO: Fetch technical indicator data
        # Fetch Indicator data from the below endpoints:
        # url = "https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/macd/{symbol}/4h/5/8/3"
        # url = "https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/rsi/{symbol}/4h/14"
        # url = "https://cryptocurrencies-technical-study.p.rapidapi.com/crypto/obv/{symbol}/4h/4"

        # Check for MACD crossover
        # A "MACD Golden Cross" occurs when the MACD line (the difference between the 12-period EMA and the 26-period EMA)
        # crosses above the signal line (the 9-period EMA of the MACD line).
        # A "MACD Death Cross" occurs when the MACD line crosses below the signal line.

        # Check for RSI overbought/oversold
        # An asset is considered overbought when the RSI is above 70%.
        # An asset is considered oversold when the RSI is below 30%.

        # Check for RSI divergence
        # there are 4 types of divergence:
        # 1. Regular Bullish Divergence
        # a. Regular Bullish Divergence occurs when the price is making lower lows (LL) but the RSI is making higher lows (HL).
        # 2. Regular Bearish Divergence
        # a. Regular Bearish Divergence occurs when the price is making higher highs (HH) but the RSI is making lower highs (LH).
        # 3. Hidden Bullish Divergence
        # a Hidden Bullish Divergence occurs when the price is making higher lows (HL) but the RSI is making lower lows (LL).
        # 4. Hidden Bearish Divergence
        # a. Hidden Bearish Divergence occurs when the price is making lower highs (LH) but the RSI is making higher highs (HH).

        # Check for OBV divergence
        # OBV divergence occurs when the price of an asset moves in one direction and the OBV indicator moves in the opposite direction.
        # If the price is rising and the OBV is flat or falling, the price may be near a top.
        # If the price is falling and the OBV is flat or rising, the price may be nearing a bottom.

        # Plot chart
        chart_file = PlotChart.plot_ohlcv_chart(symbol, "4h")

        # Update the loading message to indicate that the chart has been generated
        message.edit_text("Chart generated. Sending chart...")
        logger.info("Loading message updated")

        # Send chart to user and then delete it
        if chart_file:
            with open(chart_file, "rb") as f:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)
            os.remove(chart_file)

        # Update the loading message to indicate that the chart has been sent and the command has completed
        message.edit_text("Chart sent. Command completed.")
        logger.info("Loading message updated")
        logger.info("Stats command completed")

    @staticmethod
    def command_handler() -> CommandHandler:
        return CommandHandler("stats", StatsHandler.stats, pass_args=True)
