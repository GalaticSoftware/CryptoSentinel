from telegram import Update
from telegram.ext import CallbackContext
from database.models import User, Session
from database.management import get_or_create_user
from database.models import Session, sessionmaker

def accept_privacy_policy(update: Update, context: CallbackContext):
    query = update.callback_query
    telegram_user_id = query.from_user.id
    username = update.effective_user.username

    # Fetch or create the user from the database
    user = get_or_create_user(telegram_user_id, username)

    # Update the user's privacy policy acceptance status
    user.accepted_policy = True

    # Commit the changes to the database
    session = Session()
    session.add(user)
    session.commit()
    session.close()

    # Send a confirmation message to the user
    context.bot.send_message(
        chat_id=telegram_user_id,
        text="Thank you for accepting our privacy policy. You can now use the bot. 🎉"
        "If you want to see the privacy policy again, you can do so by doing /policy."
        "Get started by doing /help.",
    )

