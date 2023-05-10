import unittest
from unittest.mock import MagicMock, patch
from telegram import Update, User, Message
from telegram.ext import CallbackContext
from bot.handlers.premium.news import NewsHandler

class TestNewsHandler(unittest.TestCase):

    @patch.object(NewsHandler, 'fetch_crypto_news')
    def test_news_handler(self, mock_fetch_crypto_news):
        # Mock the reply_text method for the message
        def mock_reply_text(text):
            self.assertIn("Test News", text)

        # Create a dummy update and context
        dummy_user = User(id=1, first_name="Test", is_bot=False)
        dummy_message = Message(message_id=1, from_user=dummy_user, chat=None, date=None)
        dummy_message.reply_text = MagicMock(side_effect=mock_reply_text)
        dummy_update = Update(update_id=1, message=dummy_message)
        dummy_dispatcher = MagicMock()
        dummy_context = CallbackContext(dummy_dispatcher)

        mock_fetch_crypto_news.return_value = ["Test News"]

        # Call the news_handler function
        NewsHandler.news_handler(dummy_update, dummy_context)

        # Check if the reply_text method was called with the expected message
        dummy_message.reply_text.assert_called()

if __name__ == "__main__":
    unittest.main()
