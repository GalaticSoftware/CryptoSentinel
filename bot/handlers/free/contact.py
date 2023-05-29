from telegram import Update, ParseMode
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, Filters
from telegram.ext.commandhandler import CommandHandler

COLLECT_MESSAGE = 0

def contact_command(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Please send me your support message. I will forward your message to our support channel."
    )
    return COLLECT_MESSAGE


def collect_message(update: Update, context: CallbackContext) -> int:
    context.user_data['message'] = update.message.text
    context.user_data['username'] = update.message.from_user.username
    context.user_data['user_id'] = update.message.from_user.id
    send_support_message(context)
    update.message.reply_text('Your message has been sent to our support team. We will get back to you as soon as possible.')
    return ConversationHandler.END

def send_support_message(context: CallbackContext) -> None:
    print("Sending support message...")  # debug print
    support_channel_id = '-100995339845'  # use your channel ID
    username = context.user_data['username']
    user_id = context.user_data['user_id']
    user_message = context.user_data['message']
    if username:
        message = f"New support ticket from @{username} ({user_id}):\n\n{user_message}\n\nhttps://t.me/{username}"
    else:
        message = f"New support ticket from a user with ID {user_id}:\n\n{user_message}"
    try:
        context.bot.send_message(chat_id=support_channel_id, text=message)
        print("Message sent successfully!")  # debug print
    except Exception as e:
        print(f"Failed to send message: {e}")  # print the error


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END


def get_contact_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('contact', contact_command)],
        states={
            COLLECT_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, collect_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
