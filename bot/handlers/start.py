from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from users.management import get_or_create_user, update_user_access, check_user_access

class StartHandler:
    @staticmethod
    def start(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        username = update.effective_user.username

        # Create or retrieve the user from the database
        user = get_or_create_user(user_id, username)

        # Check if the user is subscribed
        has_access = check_user_access(user_id)

        # If the user is not subscribed, send a welcome message with a subscription prompt
        if not has_access:
            welcome_message = (
                "🚀 Welcome to Crypto Sentinel Bot! 🚀\n\n"
                "Your one-stop solution for the latest news, insights, and trends in the crypto market.\n\n"
                "Type /help to explore the list of commands.\n\n"
                "Unlock premium features and stay ahead of the market by subscribing now."
            )

            subscribe_button = InlineKeyboardButton("Subscribe", callback_data="subscribe")
            keyboard = InlineKeyboardMarkup.from_button(subscribe_button)

            update.message.reply_text(welcome_message, reply_markup=keyboard)

        # If the user is subscribed, send a welcome message with available commands
        else:
            welcome_message = (
                "🚀 Welcome back to Crypto Sentinel Bot! 🚀\n\n"
                "Get the most out of your crypto trading and investment journey with our comprehensive market insights.\n\n"
                "Type /help to see the list of commands."
            )

            update.message.reply_text(welcome_message)
