from telegram import Update
from telegram.ext import CallbackContext

from CryptoSentinel.bot.utils import restricted



class HelpHandler:
    @staticmethod
    @restricted
    # help command handler
    def help(update, context):
        user_id = update.message.chat_id

        help_text = (
            "🤖 Crypto Bot Commands 🤖\n\n"
            "/start - Welcome message and command list\n"
            "/help - Show this help message\n"
            "/cotd - Get LunarCrush's Coin of the Day\n"
            "/whatsup - Fetches the current list of top URLs engagement for coins, NFTs, and stocks from the LunarCrush live dashboard.\n"
            "/global_top [metric] - Fetches the top coins list ordered by the specified metric (alt_rank, galaxy_score, social_score, bullish_sentiment, or bearish_sentiment) with a weekly interval. Defaults to social_volume if no metric is provided.\n"
            "/sentiment - Displays the top coins by 24h volume along with their bullish and bearish sentiment percentages.\n"
            "/wdom - Displays the weekly dominance change for Bitcoin and Altcoins.\n"
            "/news - Fetches the latest news articles related to cryptocurrencies.\n"
            "/positions - Displays Biggest Positions on Binance Copy Trading and Compares those to Smaller Positons.\n"
            "/trader <UID> - Fetches trader information for a specific UID on Binance.\n"
        )

        update.message.reply_text(help_text)