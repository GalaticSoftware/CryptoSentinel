from telegram import Update
from telegram.ext import CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup



# Start Handler
class StartHandler:
    @staticmethod
    def start(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        username = update.effective_user.username

        # Check if the user is subscribed


        # If the user is not subscribed, send a welcome message
        welcome_message = (
            "Welcome to the Crypto Sentinel Bot! 🚀\n\n"
            "This bot provides you with the latest news and insights from the crypto market.\n\n"
            "To get started, type /help to see the list of commands."
        )

        update.message.reply_text(welcome_message)