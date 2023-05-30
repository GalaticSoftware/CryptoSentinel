from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from users.management import get_or_create_user, update_user_access, check_user_access

class StartHandler:
    OPEN_BETA_PHASE = True  # Set this to False when the open beta phase ends

    @staticmethod
    def start(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        username = update.effective_user.username

        # Create or retrieve the user from the database
        user = get_or_create_user(user_id, username)

        # Check if the user is subscribed
        has_access = check_user_access(user_id)

        # If the bot is in open beta phase, inform the user about the upcoming premium features
        if StartHandler.OPEN_BETA_PHASE:
            welcome_message = (
                "🚀 Welcome to Crypto Sentinel Bot! 🚀\n\n"
                "We're currently in our Open Beta phase. You can use all of our free features. "
                "Join the waiting list for our premium tier to get a free one-month trial once it becomes available.\n"
                "You can join the waiting list by typing /join_waitlist.\n\n"
                "Premium features will be coming soon. Join our Community Channel (https://t.me/+vDUy90wEaoVkMWUy) to stay updated and not miss out!\n\n"
                "Type /help to explore the list of commands."
            )

            update.message.reply_text(welcome_message)

        # If the bot is not in open beta phase, show the subscribe button if the user is not subscribed
        elif not has_access:
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
