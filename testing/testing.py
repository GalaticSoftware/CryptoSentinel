from CryptoSentinel.bot.handlers.free.cotd import CotdHandler
from telegram import Update, User, Message, Chat
from CryptoSentinel.testing.mock_context import MockCallbackContext

def mock_reply_text(text):
    print(text)

dummy_user = User(id=123, first_name='John', is_bot=False)
dummy_chat = Chat(id=1, type='private')
dummy_message = Message(message_id=1, from_user=dummy_user, date=None, chat=dummy_chat)
dummy_message.reply_text = mock_reply_text  # Set the mock_reply_text method for the dummy_message
update = Update(0, message=dummy_message)  # Set the dummy message for the Update object
context = MockCallbackContext()
