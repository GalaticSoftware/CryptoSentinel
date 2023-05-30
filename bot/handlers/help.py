from telegram import Update
from telegram.ext import CallbackContext

from bot.utils import log_command_usage


class HelpHandler:
    @staticmethod
    def help(update: Update, context: CallbackContext) -> None:
        command = context.args[0] if context.args else None

        # A dictionary mapping each command to its detailed help text
        command_help_text = {
            "news": "/news - Stay informed with the latest news articles related to cryptocurrencies. You can also specify the number of articles you want to view, e.g. /news 10. Use the -k flag followed by your keyword to filter the news, e.g. /news -k Bitcoin.",
            "chart": "/chart [symbol] [interval] - Plot a chart of a specific coin by its symbol and interval. Defaults to 4h if no interval is selected. Example: /chart BTCUSDT 1d. Available intervals: 1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M",
            "cotd": "/cotd - Discover LunarCrush's Coin of the Day",
            "global_top": "/global_top [metric] - Retrieve top coins by the specified metric (alt_rank or social_score) over the past week. Defaults to social_volume if not provided. Example: /global_top social_score",
            "whatsup": "/whatsup - Get the latest top URLs engagement for coins, NFTs, and stocks from LunarCrush live dashboard.",
            "gainers": "/gainers - View the top 10 coins by 24h price change.",
            "losers": "/losers - View the bottom 10 coins by 24h price change.",
            "sentiment": "/sentiment - View top coins by 24h volume along with their bullish and bearish sentiment percentages.",
            "positions": "/positions - Compare the largest positions on Binance Copy Trading to smaller ones.",
            "stats": "/stats [symbol] [timeframe]. view the latest stats for a specific coin. Example: /stats BTCUSDT 1d",
            "signal": "/signal [symbol] [timeframe] - View the latest Sentinel signal for a specific coin. Example: /signal BTCUSDT 1d",
            # "wdom": "/wdom - Track the weekly dominance change for Bitcoin and Altcoins.",
            #   "info": "/info [symbol] - Obtain detailed information about a specific coin using its symbol. Example: /info BTCUSDT",
            "set_alert": "/set_alert <Symbol> <Price_level> - Set a price alert. You will be notified when the price of the specified symbol reaches the specified level. Example: /set_alert BTCUSDT 50000",
            "list_alerts": "/list_alerts - List all your active price alerts.",
            "remove_alert": "/remove_alert <ID> - Remove a specific price alert by its ID. Example: /remove_alert 1",
        }

        if command and command in command_help_text:
            update.message.reply_text(command_help_text[command])
        else:
            help_text = (
                "🤖 Crypto Sentinel Bot 🤖\n\n"
                "🔍 /help [command] - For command details\n"
                "🚀 /start - To begin\n\n"
                "🆓 Free Commands:\n"
                "💫 /cotd - Coin of the Day\n"
                "🌐 /global_top [metric] - Top coins\n"
                "🆙 /whatsup - Trending now!\n"
                "📈 /gainers - Top 10 coins by 24h price\n"
                "📉 /losers - Bottom 10 coins by 24h price\n"
                "📰 /news - Latest crypto news\n"
                "💹 /set_alert <Symbol> <Price_level> - Set a price alert\n"
                "🔔 /list_alerts - List all your active price alerts\n"
                "🚫 /remove_alert <ID> - Remove a specific price alert\n\n"
                "🔐 Premium Commands:\n"
                "📊 /sentiment - Coin sentiments\n"
                "💹 /positions - Big Positions from Binance\n"
                "📊 /stats [symbol] [timeframe] - Coin stats\n"
                "📈 /signal [symbol] [timeframe] - Sentinel signals\n"
                # "🔍 /wdom - Bitcoin & Altcoin dominance\n"
                # "🔎 /info [symbol] - Coin info. Ex: /info BTC\n"
                "📉 /chart [symbol] [interval] - Coin chart. Ex: /chart BTCUSDT 1d.\n\n"
                "💎 How to get Premium access:\n"
                "Type /start and then click on the 'Subscribe' button. Choose your preferred payment option to get access to premium features.\n\n"
                "🆘 Support:\n"
                "If you need help,  you can contact our support team by doing:\n"
                "/contact \n"
                "and then follow the instructions provided.\n\n"
            )

            update.message.reply_text(help_text)
