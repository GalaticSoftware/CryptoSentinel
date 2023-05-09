from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from users.management import check_user_access

class StartHandler:
    @staticmethod
    def start(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        username = update.effective_user.username

        # Check if the user is subscribed
        has_access = check_user_access(user_id)

        # If the user is not subscribed, send a welcome message with a subscription prompt
        if not has_access:
            welcome_message = (
                "Welcome to the Crypto Sentinel Bot! 🚀\n\n"
                "This bot provides you with the latest news and insights from the crypto market.\n\n"
                "To access the premium features, please subscribe first."
            )

            subscribe_button = InlineKeyboardButton("Subscribe", callback_data="subscribe")
            keyboard = InlineKeyboardMarkup.from_button(subscribe_button)

            update.message.reply_text(welcome_message, reply_markup=keyboard)

        # If the user is subscribed, send a welcome message with available commands
        else:
            welcome_message = (
                "Welcome to the Crypto Sentinel Bot! 🚀\n\n"
                "This bot provides you with the latest news and insights from the crypto market.\n\n"
                "To get started, type /help to see the list of commands."
            )

            update.message.reply_text(welcome_message)
