############################
### Binance API functions###
############################


#######################################
### Binance Futures Leaderboard Bot ###
#######################################

import requests
import functools
import time
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram import ParseMode

from config.settings import X_RAPIDAPI_KEY
from config.settings import TELEGRAM_API_TOKEN
from config.settings import LUNARCRUSH_API_KEY
from bot.utils import restricted
from bot.database import Session, SummaryData
from bot.utils import log_command_usage

import logging

logger = logging.getLogger(__name__)


class PositionsHandler:
    # Define Cache decorator to cache function results for a given number of seconds to avoid hitting rate limit of the API and to speed up the bot
    def cache(seconds):
        def decorator_cache(func):
            @functools.wraps(func)
            def wrapper_cache(*args, **kwargs):
                if not hasattr(wrapper_cache, "cache"):
                    wrapper_cache.cache = {}
                key = (args, tuple(kwargs.items()))
                if (
                    key not in wrapper_cache.cache
                    or time.time() - wrapper_cache.cache[key][1] > seconds
                ):
                    result = func(*args, **kwargs)
                    wrapper_cache.cache[key] = (result, time.time())
                    return result, False
                return wrapper_cache.cache[key][0], True

            return wrapper_cache

        return decorator_cache

    # Fetch All time top traders Futures Position data
    # Cache for 2 hours
    @cache(2 * 60 * 60)
    def fetch_trader_positions(encrypted_uid):
        url = (
            "https://binance-futures-leaderboard1.p.rapidapi.com/v2/getTraderPositions"
        )
        querystring = {"encryptedUid": encrypted_uid}
        headers = {
            "X-RapidAPI-Key": X_RAPIDAPI_KEY,
            "X-RapidAPI-Host": "binance-futures-leaderboard1.p.rapidapi.com",
        }

        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json(), False
        else:
            return None, True

    position_output_dict = {}

    @restricted
    @log_command_usage("positions")
    def trader_positions(update: Update, context: CallbackContext):
        # Get the user id
        uid_list = [
            "3AFFCB67ED4F1D1D8437BA17F4E8E5ED",
            "F5335CE565C1C0712A254FB595193E84",
            "4325641055745EBAFED26DB3ACDC7AF1",
            "268BCB704E7DA7FE7EE3D228F248BDAB",
            "A086AC7B587E11941378E95DD6C872C6",
            "DA200CE4A90667D0E59FDF8E6B68E599",
            "65B136F1A727C572A5CA114F3CDC97AA",
            "36D12879856E9ABF7148BAE61E77D279",
            "87FFB710AC2792DE3145272BCBA05EBE",
            "A980D282CBFA6AC326160A5B2D879798",
            "8785BDE7F3A55E0C353ABDFE85899A26",
            "A99ACCB8798FCC1D822250364ED487AB",
            "FB7B3C9E5AE654B39231923DDB4D5260",
            "C20E7A8966C0014A4AF5774DD709DC42",
            "D3AFE978B3F0CD58489BC27B35906769",
            "F90459BB0C3BC6CE241CADAA80DEBF25",
            "E4C2BCB6FDF2A2A7A20D516B8389B952",
            "A532C4316C00206168F795EDFBB3E164",
            "21CD087408060BDD97F001B72CC2B0D3",
            "FE63D6040E22611D978B73064B3A2057",
            "B8538478A5B1907531E8EAC3BCFE0626",
            "FB23E1A8B7E2944FAAEC6219BBDF8243",
            "3EFA61BC63849632347ED020C78634E1",
            "AB995C0BACF7B0DF83AAAA61CAD3AD11",
            "6F79990013ADA8A281145D9EC2421AC3",
            "5233F02D1841D75C9DCC63D356A1758C",
            "D2EE8B6D70AAC0181B6D0AB857D6EF60",
            "F4BD136947A8A5DD4494D9A4264432B6",
            "BFE5C3E7EF7B3629438D907CD3B21D57",
            "8FE17CCE0A3EA996ED7D8B538419C826",
            "6408AAEEEBF0C76A3D5F0E39C64AAABA",
            "FB7B3C9E5AE654B39231923DDB4D5260",
            "49A7275656A7ABF56830126ACC619FEB",
        ]

        # Send a Loading message and tag it so we can delete it later
        loading_message = update.message.reply_text(
            "Fetching Positions Data From Binance... Please wait.", quote=True
        )

        total_short_below_threshold = 0
        total_long_below_threshold = 0
        total_short_above_threshold = 0
        total_long_above_threshold = 0

        for encrypted_uid in uid_list:
            try:
                data, is_cached = PositionsHandler.fetch_trader_positions(encrypted_uid)
            except Exception as e:
                logging.error(f"Error processing UID {encrypted_uid}: {str(e)}")
                continue

            if data is None:
                continue

            positions = (
                data[0].get("data", [])[0].get("positions", {}).get("perpetual", [])
                if data
                else []
            )

            if positions is None:
                continue

            whale_filter_size = 200000

            long_rows = []
            short_rows = []

            for position in positions:
                symbol = position["symbol"]
                entry_price = position["entryPrice"]
                mark_price = position["markPrice"]
                pnl = position["pnl"]
                roe = position["roe"]
                amount = position["amount"]
                leverage = position["leverage"]
                long = position["long"]
                short = position["short"]

                position_value_usd = abs(amount) * mark_price
                position_value_usd_str = "{:,.2f}".format(position_value_usd).rjust(18)

                if long:
                    if position_value_usd >= whale_filter_size:
                        long_rows.append(
                            [
                                symbol,
                                entry_price,
                                mark_price,
                                pnl,
                                roe,
                                position_value_usd_str,
                                leverage,
                            ]
                        )
                        total_long_above_threshold += position_value_usd
                    else:
                        total_long_below_threshold += position_value_usd
                elif short:
                    if position_value_usd >= whale_filter_size:
                        short_rows.append(
                            [
                                symbol,
                                entry_price,
                                mark_price,
                                pnl,
                                roe,
                                position_value_usd_str,
                                leverage,
                            ]
                        )
                        total_short_above_threshold += position_value_usd
                    else:
                        total_short_below_threshold += position_value_usd

                if not is_cached:
                    if long:
                        if position_value_usd >= whale_filter_size:
                            if [
                                symbol,
                                entry_price,
                                mark_price,
                                pnl,
                                roe,
                                position_value_usd_str,
                                leverage,
                            ] not in long_rows:
                                long_rows.append(
                                    [
                                        symbol,
                                        entry_price,
                                        mark_price,
                                        pnl,
                                        roe,
                                        position_value_usd_str,
                                        leverage,
                                    ]
                                )
                                total_long_above_threshold += position_value_usd
                        else:
                            total_long_below_threshold += position_value_usd
                    elif short:
                        if position_value_usd >= whale_filter_size:
                            if [
                                symbol,
                                entry_price,
                                mark_price,
                                pnl,
                                roe,
                                position_value_usd_str,
                                leverage,
                            ] not in short_rows:
                                short_rows.append(
                                    [
                                        symbol,
                                        entry_price,
                                        mark_price,
                                        pnl,
                                        roe,
                                        position_value_usd_str,
                                        leverage,
                                    ]
                                )
                                total_short_above_threshold += position_value_usd
                        else:
                            total_short_below_threshold += position_value_usd

            if not long_rows and not short_rows:
                continue

            if not is_cached:
                output = f"<b>UID: {encrypted_uid}</b>\n\n"

                if long_rows:
                    output += f"<b>📈 Long Positions:</b>\n"
                    for i, row in enumerate(long_rows):
                        pnl = (
                            float(row[3].replace(",", ""))
                            if isinstance(row[3], str)
                            else row[3]
                        )
                        amount = (
                            float(row[5].replace(",", ""))
                            if isinstance(row[5], str)
                            else row[5]
                        )
                        output += f"{i+1}️⃣ {row[0]}\n   💹 Entry: {float(row[1]):.5f}\n   🎯 Mark: {float(row[2]):.5f}\n   💰 PnL: ${pnl:.2f} ({float(row[4]):.2f}%)\n   🧮 Amount: ${amount:.2f}\n   ⚖️ Leverage: {row[6]}\n\n"

                if short_rows:
                    output += f"<b> 📉 Short Positions: </b>\n"
                    for i, row in enumerate(short_rows):
                        pnl = (
                            float(row[3].replace(",", ""))
                            if isinstance(row[3], str)
                            else row[3]
                        )
                        amount = (
                            float(row[5].replace(",", ""))
                            if isinstance(row[5], str)
                            else row[5]
                        )
                        output += f"{i+1}️⃣ {row[0]}\n   💹 Entry: {float(row[1]):.5f}\n   🎯 Mark: {float(row[2]):.5f}\n   💰 PnL: ${pnl:.2f} ({float(row[4]):.2f}%)\n   🧮 Amount: ${amount:.2f}\n   ⚖️ Leverage: {row[6]}\n\n"

                    PositionsHandler.position_output_dict[encrypted_uid] = output
                update.message.reply_text(output, parse_mode=ParseMode.HTML)
            else:
                if encrypted_uid in PositionsHandler.position_output_dict:
                    update.message.reply_text(
                        PositionsHandler.position_output_dict[encrypted_uid],
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    continue

        # Calculate % values of total longs and shorts for each group
        whale_percent_long = (
            total_long_above_threshold
            / (total_long_above_threshold + total_short_above_threshold)
            * 100
        )
        whale_percent_short = (
            total_short_above_threshold
            / (total_long_above_threshold + total_short_above_threshold)
            * 100
        )
        retail_percent_long = (
            total_long_below_threshold
            / (total_long_below_threshold + total_short_below_threshold)
            * 100
        )
        retail_percent_short = (
            total_short_below_threshold
            / (total_long_below_threshold + total_short_below_threshold)
            * 100
        )

        # Calculate the overall % of longs and shorts regardless of group
        total_long_percent = (
            total_long_above_threshold
            / (total_long_above_threshold + total_short_above_threshold)
            * 100
        )
        total_short_percent = (
            total_short_above_threshold
            / (total_long_above_threshold + total_short_above_threshold)
            * 100
        )

        summary = f"💡 <b>Whale vs. Retail $:</b>\n"
        summary += f"🐋 Total Whale Longs: ${total_long_above_threshold:,.2f}\n"
        summary += f"🐋 Total Whale Shorts: ${total_short_above_threshold:,.2f}\n"
        summary += f"👨‍💻 Total Retail Longs: ${total_long_below_threshold:,.2f}\n"
        summary += f"👨‍💻 Total Retail Shorts: ${total_short_below_threshold:,.2f}\n\n"
        summary += f"📈 Whale vs. Retail %\n"
        summary += f"🐋 Whale Longs: {whale_percent_long:.2f}%\n"
        summary += f"🐋 Whale Shorts: {whale_percent_short:.2f}%\n"
        summary += f"👨‍💻 Retail Longs: {retail_percent_long:.2f}%\n"
        summary += f"👨‍💻 Retail Shorts: {retail_percent_short:.2f}%\n\n"
        summary += f"📈 Total Longs vs. shorts %:\n"
        summary += f" Total Longs: {total_long_percent:.2f}%\n"
        summary += f" Total Shorts: {total_short_percent:.2f}%\n"

        update.message.reply_text(summary, parse_mode=ParseMode.HTML)

        # Delete the loading message from the chat
        context.bot.delete_message(
            chat_id=update.message.chat_id, message_id=loading_message.message_id
        )

        if not is_cached:
            # Create a new session
            session = Session()

            # Create a new SummaryData instance with the calculated values
            new_summary_data = SummaryData(
                total_whale_longs=total_long_above_threshold,
                total_whale_shorts=total_short_above_threshold,
                total_retail_longs=total_long_below_threshold,
                total_retail_shorts=total_short_below_threshold,
            )

            # Add the new summary data to the session
            session.add(new_summary_data)

            # Commit the session to save the data to the database
            session.commit()

            # Close the session
            session.close()
