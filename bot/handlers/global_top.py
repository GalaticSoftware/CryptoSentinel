import requests
import logging
from telegram import Update
from telegram.ext import CallbackContext

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
                logger.debug(response.json())
                return response.json()["top"]
            else:
                logger.error(f"Error fetching top coins data: {response.status_code}")
                return None

        def format_response_message(top_coins, metric):
            if not top_coins:
                return "An error occurred while fetching the top coins data."
            
            response_message = f"Top 10 coins by {metric}:\n\n"
            logger.debug(f"Response message before loop: {response_message}")

            for i, coin in enumerate(top_coins, start=1):
                if coin is not None and all(key in coin for key in ('symbol', 'name', 'current_price')):
                    response_message += f"{i}. {coin['symbol']} ({coin['name']}): ${coin['current_price']:.4f}\n"

            logger.debug(f"Response message after loop: {response_message}")

            if response_message:
                response_message += "\nPowered by LunarCrush"

            logger.debug(f"Response message final value: {response_message}")
            return response_message


        valid_metrics = ["alt_rank", "social_score"]
        metric = "social_volume"

        if context.args and context.args[0] in valid_metrics:
            metric = context.args[0]
        elif context.args:
            update.message.reply_text(f"Invalid metric. Using default metric: {metric}")

        top_coins = fetch_top_coins(metric)

        response_message = format_response_message(top_coins, metric)
        logger.debug(f"Response message before sending: {response_message}")
        update.message.reply_text(response_message)
