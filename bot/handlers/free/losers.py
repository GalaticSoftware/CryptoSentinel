from pycoingecko import CoinGeckoAPI
from telegram import Update
from telegram.ext import CallbackContext
import os

from bot.utils import PlotChart, log_command_usage

cg = CoinGeckoAPI()


class LosersHandler:
    @log_command_usage("losers")
    def losers(update: Update, context: CallbackContext) -> None:
        coins = cg.get_coins_markets(vs_currency="usd")
        losers = sorted(
            coins, key=lambda x: x["price_change_percentage_24h"], reverse=False
        )
        for coin in losers[:5]:
            update.message.reply_text(
                f"{coin['name']}: {coin['price_change_percentage_24h']}%"
            )
            # Convert the coin name to the symbol for the chart. For example, "Bitcoin" -> "BTCUSDT",  "Filecoin" -> "FILUSDT"
            symbol = coin["symbol"].upper() + "USDT"
            chart_file = PlotChart.plot_ohlcv_chart(symbol, "4h")
            if chart_file is not None:
                with open(chart_file, "rb") as file:
                    context.bot.send_photo(chat_id=update.effective_chat.id, photo=file)
                os.remove(chart_file)  # Delete the chart file after sending it
