import unittest
from unittest.mock import MagicMock

from telegram import Update, Message, Chat, User
from telegram.ext import CallbackContext, Dispatcher

from CryptoSentinel.bot.handlers.free.global_top import GlobalTopHandler

class TestGlobalTopHandler(unittest.TestCase):
    def test_global_top(self):
        def mock_reply_text(text):
            self.assertIn("Top 10 coins by", text)

        # Prepare mock objects
        dummy_user = User(id=123, first_name="Test", is_bot=False)
        dummy_chat = Chat(id=456, type="private")
        dummy_message = Message(
            message_id=1, from_user=dummy_user, date=None, chat=dummy_chat
        )
        dummy_message.reply_text = mock_reply_text
        dummy_update = Update(update_id=1, message=dummy_message)

        context_args = ["social_score"]  # Use a valid metric
        dummy_dispatcher = Dispatcher(None, None, use_context=True)
        dummy_context = CallbackContext(dummy_dispatcher)
        dummy_context.args = context_args

        # Run the global_top function with the mock objects
        GlobalTopHandler.global_top(dummy_update, dummy_context)


if __name__ == "__main__":
    unittest.main()
