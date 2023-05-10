import requests
from telegram import Update
from telegram.ext import CallbackContext
from config.settings import X_RAPIDAPI_KEY

from bot.utils import restricted

import logging

logger = logging.getLogger(__name__)


class NewsHandler:
    """
    NewsHandler class for handling the fetching and sending of crypto news.
    """

    @staticmethod
    def fetch_crypto_news():
        """
        Fetch the latest crypto news from the RapidAPI Crypto News API.

        :return: A list of formatted news strings
        """
        url = "https://crypto-news16.p.rapidapi.com/news/top/5"
        headers = {
            'X-RapidAPI-Key': X_RAPIDAPI_KEY,
            'X-RapidAPI-Host': "crypto-news16.p.rapidapi.com"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            news_data = response.json()
        except Exception as e:
            logger.error(f"Error fetching crypto news: {e}")
            return []

        news_list = []
        for news_item in news_data:
            title = news_item['title']
            description = news_item['description']
            url = news_item['url']
            date = news_item['date']
            formatted_news = f"{title}\n{description}\n{url}\n{date}"
            news_list.append(formatted_news)

        return news_list

    @restricted
    def news_handler(update: Update, context: CallbackContext):
        """
        Handle the /news command and send the fetched news to the user.

        :param update: Incoming update for the bot
        :param context: Context for the callback
        """
        news_list = NewsHandler.fetch_crypto_news()

        if not news_list:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Failed to fetch crypto news.")
            return

        for news in news_list:
            update.message.reply_text(news)
