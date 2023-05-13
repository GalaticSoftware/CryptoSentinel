from telegram import Update
from telegram.ext import CallbackContext

from bot.utils import log_command_usage

class HelpHandler:
    @staticmethod
    @log_command_usage
    # help command handler
    def help(update: Update, context: CallbackContext) -> None:

        help_text = (
            "🤖 Crypto Bot Commands 🤖\n\n"
            "Free Commands:\n"
            "/cotd - Get LunarCrush's Coin of the Day\n"
            "/global_top [metric] - Fetches the top coins list ordered by the specified metric (alt_rank, social_score, or social_volume) with a weekly interval. Defaults to social_volume if no metric is provided.\n"
            "Example: /global_top social_score\n\n"
            "/whatsup - Fetches the current list of top URLs engagement for coins, NFTs, and stocks from the LunarCrush live dashboard.\n\n"

            "Premium Commands:\n"
            "/sentiment - Displays the top coins by 24h volume along with their bullish and bearish sentiment percentages.\n"
            "/positions - Displays Biggest Positions on Binance Copy Trading and Compares those to Smaller Positons.\n"
            "/wdom - Displays the weekly dominance change for Bitcoin and Altcoins.\n"
            "/news - Fetches the latest news articles related to cryptocurrencies.\n"
            "/info [symbol] - Get detailed information about a specific coin by its symbol.\n"
            "Example:\n"
            "/info BTC\n"
            "/chart [symbol] [interval] - Plot a chart of a specific coin by its symbol and interval. Will default to 4h if no interval is selected.\n"
            "Example:\n"
            "/chart BTC 1d\n"
            "Available intervals: 1h, 4h, 1d, 1w\n\n"

            "Other Commands:\n"
            "/use_token [token] - Use a token to unlock premium features for a limited time.\n"
            "Example: /use_token ABCDEFGHIJKLMNOP\n"
        )

        update.message.reply_text(help_text)
