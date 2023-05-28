import requests
from telegram import Update
from telegram.ext import CallbackContext
import logging

from bot.utils import log_command_usage
from config.settings import LUNARCRUSH_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WhatsupHandler class definition
# This class contains the implementation of the /whatsup command handler.
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
            response.raise_for_status()  # Raises stored HTTPError, if one occurred.
            response_data = response.json()

            # Log the response data for debugging
            logger.info("Response data from LunarCrush API: %s", response_data)

            # Check if the response data is generated successfully
            if response_data['config']['generated']:
                # Process and format the data
                coins_data = response_data['data']['coins']['urls_engagement']
                message = "Top URLs engagement:\n\n"
                for coin in coins_data:
                    message += f"{coin['meta']['title']}: {coin['meta']['url']}\n"

                # Log the formatted message for debugging
                logger.info("Formatted message: %s", message)

                # Send the message to the user
                update.message.reply_text(message)
            else:
                # Notify the user if there's an error fetching data from LunarCrush API
                update.message.reply_text("Error fetching data from LunarCrush API.")
                logger.error("Error fetching data from LunarCrush API. Response data: %s", response_data)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f'HTTP error occurred: {http_err}')
            update.message.reply_text("An HTTP error occurred while processing the /whatsup command.")
        except requests.exceptions.RequestException as req_err:
            logger.error(f'Request error occurred: {req_err}')
            update.message.reply_text("A network error occurred while processing the /whatsup command.")
        except Exception as e:
            logger.exception("An error occurred while processing the /whatsup command: %s", e)
            update.message.reply_text("An error occurred while processing the /whatsup command.")
