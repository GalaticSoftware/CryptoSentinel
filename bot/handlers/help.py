from telegram import Update
from telegram.ext import CallbackContext

from bot.utils import log_command_usage

class HelpHandler:
    @staticmethod
    def help(update: Update, context: CallbackContext) -> None:
        help_text = (
            "🤖 Crypto Sentinel Bot Commands 🤖\n\n"
            "🆓 Free Commands:\n"
            "/cotd - Discover LunarCrush's Coin of the Day\n"
            "/global_top [metric] - Retrieve top coins by the specified metric (alt_rank, social_score, or social_volume) over the past week. Defaults to social_volume if not provided.\n"
            "Example: /global_top social_score\n"
            "/whatsup - Get the latest top URLs engagement for coins, NFTs, and stocks from LunarCrush live dashboard.\n"
            "/gainers - View the top 10 coins by 24h price change.\n"
            "/losers - View the bottom 10 coins by 24h price change.\n\n"
            
            
            "🔐 Premium Commands:\n"
            "/sentiment - View top coins by 24h volume along with their bullish and bearish sentiment percentages.\n"
            "/positions - Compare the largest positions on Binance Copy Trading to smaller ones.\n"
            "/wdom - Track the weekly dominance change for Bitcoin and Altcoins.\n"
            "/news - Stay informed with the latest news articles related to cryptocurrencies. You can also specify the number of articles you want to view, e.g. /news 10. Use the -k flag followed by your keyword to filter the news, e.g. /news -k Bitcoin.\n"
            "/info [symbol] - Obtain detailed information about a specific coin using its symbol. Example: /info BTC\n"
            "/chart [symbol] [interval] - Plot a chart of a specific coin by its symbol and interval. Defaults to 4h if no interval is selected. Example: /chart BTC 1d. Available intervals: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M\n\n"
        )

        update.message.reply_text(help_text)
