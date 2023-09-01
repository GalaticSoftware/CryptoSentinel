from pycoingecko import CoinGeckoAPI
from telegram import Update
from telegram.ext import CallbackContext
import os

from bot.utils import PlotChart, log_command_usage

cg = CoinGeckoAPI()


class GainersHandler:
    @log_command_usage("gainers")
    def gainers(update: Update, context: CallbackContext) -> None:
        coins = cg.get_coins_markets(vs_currency="usd")
        gainers = sorted(
            coins, key=lambda x: x["price_change_percentage_24h"], reverse=True
        )
        for coin in gainers[:5]:
            update.message.reply_text(
                f"{coin['name']}: {coin['price_change_percentage_24h']}%"
            )
            loading_message = update.message.reply_text(
                f"Loading OHLCV chart for {coin['name']}...", quote=True
            )
            # Convert the coin name to the symbol for the chart. For example, "Bitcoin" -> "BTCUSDT",  "Filecoin" -> "FILUSDT"
            symbol = coin["symbol"].upper() + "USDT"
            chart_file = PlotChart.plot_ohlcv_chart(symbol, "4h")

            # if chart_file is None delete the loading message, send a symbol not found message and continue to the next coin
            if chart_file is None:
                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id,
                )
                update.message.reply_text(
                    f"Symbol not listed on available exchanges."
                )
                continue

            if chart_file is not None:
                with open(chart_file, "rb") as file:
                    context.bot.send_photo(
                        chat_id=update.effective_chat.id, photo=file)
                os.remove(chart_file)  # Delete the chart file after sending it

                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=loading_message.message_id,
                )
