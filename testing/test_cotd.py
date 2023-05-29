import unittest
from telegram import Update, User, Message, Chat
from bot.handlers.free.cotd import CotdHandler
from mock_context import MockCallbackContext
from unittest.mock import patch, MagicMock
from telegram.ext import CallbackContext
from datetime import datetime
from telegram.ext import Dispatcher, CallbackContext
from telegram import Bot
from unittest.mock import Mock
from config.settings import LUNARCRUSH_API_KEY
import asyncio
import requests
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCotdHandler(unittest.TestCase):
    @patch('bot.handlers.free.cotd.CotdHandler.plot_ohlcv_chart', side_effect=lambda _: open('charts/BTC_chart.png', 'w').close())
    @patch('requests.get')
    def test_coin_of_the_day(self, mock_get, mock_plot, mock_context):
        # Create a mock response for the LunarCrush API call
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Bitcoin", "symbol": "BTC"}
        mock_get.return_value = mock_response

        # Create a mock Dispatcher, Bot and pass them to the CallbackContext
        mock_dispatcher = Mock(Dispatcher)
        mock_bot = Mock(Bot)
        mock_context = CallbackContext(dispatcher=mock_dispatcher, bot=mock_bot)


        # Create a mock update and context
        mock_update = Update(update_id=123, message=Message(message_id=1, date=datetime.now(), chat=Chat(id=1, type='private'), from_user=User(id=1, first_name='Test', is_bot=False)))

        # Create a mock Dispatcher and pass it to the CallbackContext
        mock_dispatcher = Mock(Dispatcher)
        mock_context = CallbackContext(mock_dispatcher)

        # Call the coin_of_the_day function
        asyncio.run(CotdHandler.coin_of_the_day(mock_update, mock_context))

        # Check that the LunarCrush API was called correctly
        mock_get.assert_called_once_with("https://lunarcrush.com/api3/coinoftheday", headers={"Authorization": f"Bearer {LUNARCRUSH_API_KEY}"})

        # Check that the plot_ohlcv_chart function was called correctly
        mock_plot.assert_called_once_with("BTC")

        # Check that the message was sent correctly
        mock_context.bot.send_photo.assert_called_once()
        mock_context.bot.send_message.assert_called_once_with(chat_id=mock_update.effective_chat.id, text="Coin of the Day: Bitcoin (BTC)")

if __name__ == '__main__':
    unittest.main()