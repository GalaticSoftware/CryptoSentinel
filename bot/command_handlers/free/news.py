import requests
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from config.settings import X_RAPIDAPI_KEY
from bot.utils import log_command_usage, privacy_policy_accepted
import logging

logger = logging.getLogger(__name__)

class NewsHandler:
    """
    NewsHandler class for handling the fetching and sending of crypto news.
    """

    @staticmethod
    def fetch_crypto_news(source=None, keyword=None, limit=5):
        """
        Fetch the latest crypto news from the RapidAPI Crypto News API.

        :param source: The news source to filter by, or None to get all news
        :param keyword: The keyword to filter by, or None to get all news
        :param limit: The number of news items to fetch
        :return: A list of formatted news strings
        """
        if source:
            url = f"https://crypto-news16.p.rapidapi.com/news/{source}/{limit}"
        else:
            url = f"https://crypto-news16.p.rapidapi.com/news/top/{limit}"

        headers = {
            'X-RapidAPI-Key': X_RAPIDAPI_KEY,
            'X-RapidAPI-Host': "crypto-news16.p.rapidapi.com"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logger.error(f"Http Error: {errh}")
            return []
        except requests.exceptions.ConnectionError as errc:
            logger.error(f"Error Connecting: {errc}")
            return []
        except requests.exceptions.Timeout as errt:
            logger.error(f"Timeout Error: {errt}")
            return []
        except requests.exceptions.RequestException as err:
            logger.error(f"Something went wrong: {err}")
            return []

        news_data = response.json()
        news_list = []
        for news_item in news_data:
            title = news_item['title']
            description = news_item['description']
            url = news_item['url']
            date = news_item['date']
            if keyword and (keyword.lower() not in title.lower() and keyword.lower() not in description.lower()):
                continue
            formatted_news = f"*{title}*\n{description}\n[Read More]({url})\n{date}"
            news_list.append(formatted_news)

        logger.debug(f"Received news data: {news_data}")
        logger.debug(f"Created news list: {news_list}")

        return news_list


    @log_command_usage("news")
    @privacy_policy_accepted
    def news_handler(update: Update, context: CallbackContext):
        """
        Handle the /news command and send the fetched news to the user.

        :param update: Incoming update for the bot
        :param context: Context for the callback
        """
        logger.info(f"Received /news command with args: {context.args}")
        source, keyword, limit = None, None, 5
        if context.args:
            source = context.args[0] if context.args[0] in ['CoinDesk', 'CoinTelegraph', 'CoinJournal', 'CryptoNinjas', 'YahooFinance', 'all'] else None
            keyword = context.args[1] if len(context.args) > 1 else None
            if context.args[-1].isdigit():
                limit = int(context.args[-1])

        news_list = NewsHandler.fetch_crypto_news(source, keyword, limit)

        if not news_list:
            logger.error("Failed to fetch crypto news. news_list is empty.")
            context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to fetch crypto news.")
            return

        logger.info(f"Sending {len(news_list)} news items to the user.")
        for news in news_list:
            update.message.reply_text(news, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
        
        logger.info("Finished sending news to the user.")
