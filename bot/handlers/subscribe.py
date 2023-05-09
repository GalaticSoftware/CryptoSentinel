from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler

from users.management import get_or_create_user, update_user_access


import logging



class SubscribeHandler:
    def subscribe(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        # Get the user's Telegram ID
        user_id = update.effective_user.id
        username = update.effective_user.username

        # Create or retrieve the user from the database
        user = get_or_create_user(user_id, username)

        # Update the user's access status in the database
        update_user_access(user_id, has_access=True)

        # Add logging
        logging.info(f"User {username} (ID: {user_id}) subscribed")

        # Add your subscription process here (if you have additional steps)

        query.edit_message_text("Thank you for subscribing! You now have access to all features.")

    subscribe_handler = CallbackQueryHandler(subscribe, pattern="^subscribe$")