import logging
from typing import List

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
)

from config.settings import TELEGRAM_IDS

logger = logging.getLogger(__name__)


class ContactHandler:
    @staticmethod
    def contact(update: Update, context: CallbackContext):
        update.message.reply_text(
            "Please enter your message. You can cancel this conversation at any time by typing /cancel."
        )
        return "get_message"

    @staticmethod
    def conversation_handler() -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("contact", ContactHandler.contact)],
            states={
                "get_message": [
                    MessageHandler(
                        Filters.text & ~Filters.command,
                        ContactHandler.message,
                    )
                ],
                "confirm_message": [
                    CommandHandler("confirm", ContactHandler.confirm_message),
                    CommandHandler("cancel", ContactHandler.cancel),
                ],
            },
            fallbacks=[
                CommandHandler("cancel", ContactHandler.cancel),
                MessageHandler(Filters.all, ContactHandler.error),
            ],
        )

    @staticmethod
    def message(update: Update, context: CallbackContext):
        if len(update.message.text) > 4096:
            update.message.reply_text(
                "Your message is too long. Please limit it to 4096 characters."
            )
            return "get_message"
        context.user_data["message"] = update.message.text
        update.message.reply_text(
            "Please confirm your message by typing /confirm or change it by typing /cancel."
        )
        return "confirm_message"

    @staticmethod
    def cancel(update: Update, context: CallbackContext):
        update.message.reply_text("Conversation cancelled.")
        return ConversationHandler.END

    @staticmethod
    def confirm_message(update: Update, context: CallbackContext):
        message = context.user_data["message"]
        username = update.message.from_user.username
        if username is None:
            link = "User profile not available"
        else:
            link = f"https://t.me/{username}"
        text = f"New message from {username} ({link}):\n\n{message}"
        telegram_ids: List[int] = [
            int(telegram_id.strip()) for telegram_id in TELEGRAM_IDS.split(",")
        ]
        for telegram_id in telegram_ids:
            context.bot.send_message(chat_id=telegram_id, text=text)
        update.message.reply_text("Your message has been sent.")
        return ConversationHandler.END

    @staticmethod
    def error(update: Update, context: CallbackContext):
        logger.warning(f"Update {update} caused error {context.error}")
        update.message.reply_text("An error occurred.")
        return ConversationHandler.END
