import requests
from telegram import Update
from telegram.ext import CallbackContext
import logging
import datetime
from datetime import datetime
import cachetools

from bot.utils import log_command_usage
from config.settings import LUNARCRUSH_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the WhatsupHandler class


class WhatsupHandler:
    """
    Handles the /whatsup command, which fetches the top URLs engagement data
    for cryptocurrencies from the LunarCrush API.
    """

    @staticmethod
    @log_command_usage("whatsup")
    def whatsup(update: Update, context: CallbackContext):
        """
        Fetches and sends the top URLs engagement data to the user.

        Args:
            update (telegram.Update): The update object containing the message data.
            context (telegram.ext.CallbackContext): The context object containing additional data.
        """
        # Define the API URL and headers
        url = "https://lunarcrush.com/api3/whatsup"
        headers = {"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"}

        try:
            # Fetch the data from the LunarCrush API
            response = requests.get(url, headers=headers, timeout=20)
            # Raises stored HTTPError, if one occurred.
            response.raise_for_status()
            response_data = response.json()

            # Log the response data for debugging
            logger.debug(
                "Response data from LunarCrush API: %s", response_data)

            # Check if the response data is generated successfully
            if response_data['config']['generated']:
                # Process and format the data
                coins_data = response_data['data']['coins']['urls_engagement']

                # Filter out duplicate entries based on URL
                unique_coins_data = []
                seen_urls = set()
                for coin in coins_data:
                    url = coin['meta']['url']
                    if url not in seen_urls:
                        unique_coins_data.append(coin)
                        seen_urls.add(url)

                message = "🚀 Top URLs Engagement for Cryptocurrencies 🚀\n\n"
                for coin in unique_coins_data:
                    # Convert timestamp to human-readable format
                    timestamp = datetime.fromtimestamp(coin['meta']['time'])
                    message += f"🔗 Title: {coin['meta']['title']}\n"
                    message += f"🌐 URL: {coin['meta']['url']}\n"
                    message += f"📈 Engagement Value: {coin['value']}\n"
                    message += f"🕒 Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

                # Log the formatted message for debugging
                logger.debug("Formatted message: %s", message)

                # Send the message to the user
                update.message.reply_text(message)
            else:
                # Notify the user if there's an error fetching data from LunarCrush API
                update.message.reply_text(
                    "Error fetching data from LunarCrush API. Please try again later.")
                logger.error(
                    "Error fetching data from LunarCrush API. Response data: %s", response_data)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err}')
            update.message.reply_text(
                "An HTTP error occurred while processing the /whatsup command. Please try again later.")
        except requests.exceptions.RequestException as req_err:
            logger.error(f'Request error occurred: {req_err}')
            update.message.reply_text(
                "A network error occurred while processing the /whatsup command. Please check your connection and try again.")
        except Exception as e:
            logger.exception(
                "An error occurred while processing the /whatsup command: %s", e)
            update.message.reply_text(
                "An unexpected error occurred while processing the /whatsup command. Please try again later.")
