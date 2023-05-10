import unittest
from unittest.mock import MagicMock

from telegram import Update, User, Message, Chat
from mock_context import MockCallbackContext

from CryptoSentinel.bot.handlers.free.sentiment import SentimentHandler

def mock_reply_text(text):
    print(text)

class TestSentimentHandler(unittest.TestCase):
    def setUp(self):
        # Create a dummy message object
        dummy_user = User(id=123, first_name='John', is_bot=False)
        dummy_chat = Chat(id=1, type='private')
        dummy_message = Message(message_id=1, from_user=dummy_user, date=None, chat=dummy_chat)
        dummy_message.reply_text = mock_reply_text
        self.update = Update(0, message=dummy_message)
        self.context = MockCallbackContext()

    # test sentiment function
    def test_sentiment(self):
        SentimentHandler.sentiment(self.update, self.context)

if __name__ == "__main__":
    unittest.main()
