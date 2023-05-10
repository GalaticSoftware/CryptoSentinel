import unittest
from telegram import Update, User, Message, Chat
from bot.handlers.cotd import CotdHandler
from mock_context import MockCallbackContext

def mock_reply_text(text):
    print(text)

class TestCotdHandler(unittest.TestCase):
    
    def setUp(self):
        dummy_user = User(id=123, first_name='John', is_bot=False)
        dummy_chat = Chat(id=1, type='private')
        dummy_message = Message(message_id=1, from_user=dummy_user, date=None, chat=dummy_chat)
        dummy_message.reply_text = mock_reply_text
        self.update = Update(0, message=dummy_message)
        self.context = MockCallbackContext()

    def test_coin_of_the_day(self):
        CotdHandler.coin_of_the_day(self.update, self.context)

if __name__ == '__main__':
    unittest.main()
