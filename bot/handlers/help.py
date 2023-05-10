from telegram import Update
from telegram.ext import CallbackContext



class HelpHandler:
    @staticmethod
    # help command handler
    def help(update, context):

        help_text = (
            "🤖 Crypto Bot Commands 🤖\n\n"
            "Free Commands:\n"
            "/cotd - Get LunarCrush's Coin of the Day\n"
            "/global_top [metric] - Fetches the top coins list ordered by the specified metric (alt_rank, social_score, or social_volume) with a weekly interval. Defaults to social_volume if no metric is provided.\n"
            "/whatsup - Fetches the current list of top URLs engagement for coins, NFTs, and stocks from the LunarCrush live dashboard.\n\n"


            "Premium Commands:\n"
            "/sentiment - Displays the top coins by 24h volume along with their bullish and bearish sentiment percentages.\n"
            "/positions - Displays Biggest Positions on Binance Copy Trading and Compares those to Smaller Positons.\n"
            "/wdom - Displays the weekly dominance change for Bitcoin and Altcoins.\n"
            "/news - Fetches the latest news articles related to cryptocurrencies.\n\n"
        )

        update.message.reply_text(help_text)