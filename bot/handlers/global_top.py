import requests
import logging
from telegram import Update
from telegram.ext import CallbackContext

from bot.utils import restricted

from config.settings import LUNARCRUSH_API_KEY

logger = logging.getLogger(__name__)

class GlobalTopHandler:
    @staticmethod
    def global_top(update: Update, context: CallbackContext):
        def fetch_top_coins(metric):
            api_url = "https://lunarcrush.com/api3/coins/global/top"
            headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
            params = {
                "interval": "1w",
                "order_by": metric,
                "limit": 10,
            }
            response = requests.get(api_url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()["top"]
            else:
                logger.error(f"Error fetching top coins data: {response.status_code}")
                return None

        def format_response_message(top_coins, metric):
            if not top_coins:
                return "An error occurred while fetching the top coins data."
            
            response_message = f"Top 10 coins by {metric}:\n\n"
            for i, coin in enumerate(top_coins, start=1):
                response_message += f"{i}. {coin['symbol']} ({coin['name']}): ${coin['current_price']:.4f}\n"
            response_message += "\nPowered by LunarCrush"
            return response_message

        valid_metrics = [
            "alt_rank", "galaxy_score", "social_score",
            "bullish_sentiment", "bearish_sentiment"
        ]
        metric = "social_volume"

        if context.args and context.args[0] in valid_metrics:
            metric = context.args[0]
        elif context.args:
            update.message.reply_text(f"Invalid metric. Using default metric: {metric}")

        top_coins = fetch_top_coins(metric)
        response_message = format_response_message(top_coins, metric)
        update.message.reply_text(response_message)
