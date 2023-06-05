import requests
from telegram import Update
from telegram.ext import CallbackContext

from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted
from bot.utils import log_command_usage, command_usage_example, privacy_policy_accepted
import logging

logger = logging.getLogger(__name__)


class WdomHandler:
    """
    Weekly Dominance Change Handler class.
    This class contains the implementation of the weekly dominance change handler.
    """

    @staticmethod
    def fetch_weekly_dom_change(url, key, headers):
        """
        Fetch weekly dominance change data from LunarCrush API.

        :param url: URL for the API request
        :param key: Key to access the required data from API response
        :param headers: Headers for the API request
        :return: Weekly dominance change data or None if an error occurs
        """
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            if data['config']['generated']:
                return data[key]

        except Exception as e:
            logger.error(f"Error fetching weekly dominance change: {e}")

        return None

    @log_command_usage("wdom")
    @restricted
    @privacy_policy_accepted
    def wdom_handler(update: Update, context: CallbackContext):
        """
        Handle the /weekly_dom_change command and send the response to the user.

        :param update: Incoming update for the bot
        :param context: Context for the callback
        """
        try:
            # Define the URL and headers for fetching the weekly dominance change data
            coins_url = "https://lunarcrush.com/api3/coins/global/change"
            headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}
            dom_data = WdomHandler.fetch_weekly_dom_change(coins_url, 'data', headers)

            # Retrieve only the required fields
            dom = [{
                'name': 'Altcoins',
                'percent_change_7d': dom_data['altcoin_dominance_1w_percent_change']
            }, {
                'name': 'Bitcoin',
                'percent_change_7d': dom_data['btc_dominance_1w_percent_change']
            }]

            # Format the message and send it to the user
            message = "Weekly Dominance:\n\n"
            for idx, coin in enumerate(dom):
                message += f"{idx + 1}. Weekly {coin['name']} Dominance {coin['percent_change_7d']:.2f}%\n"

            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        except Exception as e:
            logger.error(f"Error handling /weekly_dom_change command: {e}")
            context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to fetch weekly dominance change.")
