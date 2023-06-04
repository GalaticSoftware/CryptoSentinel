import pytest
from unittest import mock
import pandas as pd
from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handlers.premium.stats import SymbolOHLCVFetcher, StatsHandler
# Create Telgram Bot Module Mock
from bot.bot_instance import bot, updater

@pytest.fixture
def ohlcv_data():
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime([1622649600000, 1622563200000], unit="ms"),
            "open": [37477.14, 36477.14],
            "high": [38029.99, 37029.99],
            "low": [36712.81, 35712.81],
            "close": [37932.96, 36932.96],
            "volume": [33334.184209, 33344.184209],
        }
    )

@mock.patch("requests.get")
def test_stats_handler(mock_get, ohlcv_data):
    symbol = "BTCUSDT"
    timeframe = "1d"
    patterns = {
        "pattern1": True,
        "pattern2": True,
        "pattern3": False,
    }
    pattern_data = {"timestamp": 123456789, "symbol": "BTC", "timeframe": "1d", "prices": [], **patterns}
    rsi_data = {"rsi": [80]}
    obv_data = {"obv": [300000]}
    mfi_data = {"mfi": [60]}
    macd_data = {"macd": [{"histogram": 10}, {"histogram": 20}]}
    mock_get.side_effect = [
        mock.MagicMock(status_code=200, json=pattern_data),
        mock.MagicMock(status_code=200, json=rsi_data),
        mock.MagicMock(status_code=200, json=obv_data),
        mock.MagicMock(status_code=200, json=mfi_data),
        mock.MagicMock(status_code=200, json=macd_data),
    ]
    update = mock.MagicMock(spec=Update)
    context = mock.MagicMock(spec=CallbackContext)
    with mock.patch("bot.stats.SymbolOHLCVFetcher.fetch_ohlcv_data") as fetch_ohlcv_mock:
        fetch_ohlcv_mock.return_value = ohlcv_data
        StatsHandler.stats(update, context)
        fetch_ohlcv_mock.assert_called_with(symbol, timeframe)
    assert update.message.reply_text.call_count == 9
    assert update.message.reply_text.call_args_list == [
        mock.call("Latest RSI: 80. RSI is in normal range"),
        mock.call("RSI Divergence: No Divergence"),
        mock.call("Latest OBV: 300000. OBV is rising"),
        mock.call("OBV Divergence: No Divergence"),
        mock.call("Latest MFI: 60. MFI is in normal range"),
        mock.call("MACD histogram is rising"),
        mock.call("MACD histogram is rising"),
        mock.call("Generating chart..."),
        mock.call("Sending chart..."),
    ]

@mock.patch("requests.get")
def test_symbol_ohlcv_fetcher(mock_get):
    symbol = "BTCUSDT"
    timeframe = "1d"
    ohlcv = [
        [1622649600000, 37477.14, 38029.99, 36712.81, 37932.96, 33334.184209],
        [1622563200000, 36477.14, 37029.99, 35712.81, 36932.96, 33344.184209],
    ]
    mock_get.return_value.json.return_value = ohlcv
    result = SymbolOHLCVFetcher.fetch_ohlcv_data(symbol, timeframe)
    assert result.equals(pd.DataFrame(
        {
            "timestamp": pd.to_datetime([1622649600000, 1622563200000], unit="ms"),
            "open": [37477.14, 36477.14],
            "high": [38029.99, 37029.99],
            "low": [36712.81, 35712.81],
            "close": [37932.96, 36932.96],
            "volume": [33334.184209, 33344.184209],
        }
    ))

