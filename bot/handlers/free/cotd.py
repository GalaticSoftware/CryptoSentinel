import requests
import logging
from telegram import Update
from telegram.ext import CallbackContext

from bot.utils import restricted
from config.settings import LUNARCRUSH_API_KEY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CotdHandler:
    @staticmethod
    def coin_of_the_day(update: Update, context: CallbackContext):
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
            update.message.reply_text(f"Coin of the Day: {coin_name} ({coin_symbol})")
        else:
            logger.error("Error in LunarCrush API response: Required data not found")
            update.message.reply_text("Error fetching Coin of the Day data. Please try again later.")


# Simple test for the coin_of_the_day method
def test_coin_of_the_day():
    url = "https://lunarcrush.com/api3/coinoftheday"
    headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    assert "name" in data and "symbol" in data

if __name__ == "__main__":
    test_coin_of_the_day()
    print("Test passed.")
