import unittest
from unittest.mock import MagicMock
from telegram import Update, User, Message
from telegram.ext import CallbackContext
from CryptoSentinel.bot.handlers.premium.whatsup import WhatsupHandler

class TestWhatsupHandler(unittest.TestCase):
    def test_whatsup(self):
        # Mock the reply_text method for the message
        def mock_reply_text(text):
            self.assertIn("Top URLs engagement", text)

        # Create a dummy update and context
        dummy_user = User(id=1, first_name="Test", is_bot=False)
        dummy_message = Message(message_id=1, from_user=dummy_user, chat=None, date=None)
        dummy_message.reply_text = MagicMock(side_effect=mock_reply_text)
        dummy_update = Update(update_id=1, message=dummy_message)
        dummy_dispatcher = MagicMock()
        dummy_context = CallbackContext(dummy_dispatcher)

        # Call the whatsup function
        WhatsupHandler.whatsup(dummy_update, dummy_context)

        # Check if the reply_text method was called with the expected message
        dummy_message.reply_text.assert_called()


if __name__ == "__main__":
    unittest.main()
