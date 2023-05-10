import unittest
from unittest.mock import MagicMock, patch
from telegram import Update
from telegram.ext import CallbackContext

from bot.handlers.premium.wdom import WdomHandler

class TestWdomHandler(unittest.TestCase):

    def test_fetch_weekly_dom_change_success(self):
        url = "https://lunarcrush.com/api3/coins/global/change"
        key = "data"
        headers = {"Authorization": "Bearer API_KEY"}

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "config": {"generated": True},
            key: {
                "altcoin_dominance_1w_percent_change": 2.58,
                "btc_dominance_1w_percent_change": -2.93,
            },
        }

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = WdomHandler.fetch_weekly_dom_change(url, key, headers)

        self.assertIsNotNone(result)
        self.assertEqual(result["altcoin_dominance_1w_percent_change"], 2.58)
        self.assertEqual(result["btc_dominance_1w_percent_change"], -2.93)

    def test_fetch_weekly_dom_change_failure(self):
        url = "https://lunarcrush.com/api3/coins/global/change"
        key = "data"
        headers = {"Authorization": "Bearer API_KEY"}

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("Failed to fetch data")

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = WdomHandler.fetch_weekly_dom_change(url, key, headers)

        self.assertIsNone(result)

    def test_wdom_handler(self):
        # Create a mock Update object
        mock_update = MagicMock(spec=Update)
        mock_update.effective_chat.id = 1

        # Create a mock CallbackContext object
        mock_context = MagicMock(spec=CallbackContext)
        mock_context.bot.send_message = MagicMock()

        with patch("bot.handlers.premium.wdom.WdomHandler.fetch_weekly_dom_change") as mock_fetch:
            mock_fetch.return_value = {
                "altcoin_dominance_1w_percent_change": 2.58,
                "btc_dominance_1w_percent_change": -2.93,
            }
            
            with patch("bot.utils.check_user_access") as mock_check_user_access:
                mock_check_user_access.return_value = True
                WdomHandler.wdom_handler(mock_update, mock_context)

        # Check if the message was sent
        mock_context.bot.send_message.assert_called_once()

        # Check if the message content is correct
        message = "Weekly Dominance:\n\n1. Weekly Altcoins Dominance 2.58%\n2. Weekly Bitcoin Dominance -2.93%\n"
        mock_context.bot.send_message.assert_called_with(chat_id=1, text=message)




if __name__ == "__main__":
    unittest.main()
