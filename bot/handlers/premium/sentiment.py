import requests
import logging
from telegram import Update
from telegram.ext import CallbackContext

from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted
from bot.utils import log_command_usage

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SentimentHandler:
    @staticmethod
    @restricted
    @log_command_usage("sentiment")
    def sentiment(update: Update, context: CallbackContext):
        logger.info("Received /sentiment command")

        # Prepare API parameters
        api_url = "https://lunarcrush.com/api3/coins/global/top"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
        params = {"interval": "1w", "order_by": "volume_24h", "limit": 10}

        # Make the API request
        response = requests.get(api_url, headers=headers, params=params)

        # Process the response
        if response.status_code == 200:
            data = response.json()
            top_coins = data["top"]

            # Format the response message
            response_message = "Top Coins by 24h Volume:\n"
            for coin in top_coins:
                volume = (
                    f"Volume: ${coin['volume_24h']:.4f}\n"
                    if "volume_24h" in coin and coin["volume_24h"] is not None
                    else ""
                )
                bullish_pct = coin["bullish_sentiment"] / coin["social_volume"] * 100
                bearish_pct = coin["bearish_sentiment"] / coin["social_volume"] * 100
                social_volume = (
                    "{:,}".format(coin["social_volume"])
                    if coin["social_volume"] is not None
                    else "N/A"
                )
                response_message += f"{volume}{coin['symbol']} {bullish_pct:.0f}% Bull {bearish_pct:.0f}% Bear\n"
        else:
            logger.error(
                f"Error fetching top coins data. Status code: {response.status_code}"
            )
            response_message = "An error occurred while fetching the top coins data."

        # Send the response message
        update.message.reply_text(response_message)
