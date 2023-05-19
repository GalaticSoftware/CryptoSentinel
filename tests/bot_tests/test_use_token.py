import unittest
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from bot.handlers.free.use_token import UseTokenHandler
from bot.database import OneTimeToken, User


class MockUpdate:
    def __init__(self, update_id, user_id, username):
        self.update_id = update_id
        self.effective_user = MagicMock()
        self.effective_user.id = user_id
        self.effective_user.username = username
        self.message = MagicMock()



class TestUseTokenHandler(unittest.TestCase):

    def setUp(self):
        # Mock the Update object
        self.update = MockUpdate(update_id=0, user_id=12345, username='test_user')
        self.update.effective_user = MagicMock()
        self.update.effective_user.id = 12345
        self.update.effective_user.username = 'test_user'
        self.update.message = MagicMock()

        # Mock the CallbackContext object
        self.context = CallbackContext(MagicMock())
        self.context.args = ['081f8d44-0dbb-40f6-b88e-726cdad1b6dc']

        # Create mock_token and mock_user
        self.mock_token = MagicMock(spec=OneTimeToken)
        self.mock_user = MagicMock(spec=User)

    # Create a new mock session class to return a mock session object with a custom query method.
    # This custom query method should simulate the query method of a real SQLAlchemy session, allowing you to control its behavior for testing purposes.
    # In the query method, you should return a mock query object that simulates the behavior of an actual SQLAlchemy query object.
    # Specifically, you'll want to create mock methods for the filter_by and first methods.
    # Modify the setUp method in the TestUseTokenHandler class to use this new mock session class instead of the original Session.
    # Finally, in the test_use_token_success method, you should be able to check if the token has been marked as used by examining the mock token object.
    @patch('bot.database.Session')
    def test_use_token_success(self, mock_session_class):
        # Set the required attributes for mock_token and mock_user
        self.mock_token.used = False
        self.mock_token.expiration_time = datetime.utcnow() + timedelta(days=1)
        self.mock_user.has_access = False

        # Create a mock session and set up its return value
        mock_session = mock_session_class.return_value
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [self.mock_token, self.mock_user]

        # Call the use_token method
        UseTokenHandler.use_token(self.update, self.context)

        # Ccheck if the token has been marked as used by examining the mock token object.
        self.assertTrue(self.mock_token.used)

        

    @patch('bot.database.Session')
    def test_use_token_failure(self, mock_session_class):
        test_cases = [
            {'desc': "Token is expired", 'token_used': False, 'token_exp_time': datetime.utcnow() - timedelta(days=1)},
            {'desc': "Token is already used", 'token_used': True, 'token_exp_time': datetime.utcnow() + timedelta(days=1)},
        ]

        for test_case in test_cases:
            with self.subTest(msg=test_case['desc']):
                # Set the required attributes for mock_token and mock_user
                self.mock_token.used = test_case['token_used']
                self.mock_token.expiration_time = test_case['token_exp_time']
                self.mock_user.has_access = False

                # Create a mock session and set up its return value
                mock_session = mock_session_class.return_value
                mock_session.query.return_value.filter_by.return_value.first.side_effect = [self.mock_token, self.mock_user]

                # Call the use_token method
                UseTokenHandler.use_token(self.update, self.context)

                # Check if the token was not marked as used and the user's access was not granted
                self.assertEqual(self.mock_token.used, test_case['token_used'])
                self.assertFalse(self.mock_user.has_access)


if __name__ == '__main__':
    unittest.main()
