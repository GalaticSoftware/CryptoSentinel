from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from users.management import check_user_access

import functools
from database import Session, CommandUsage

def restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id == 1:  # bypass restriction for test user
            return func(update, context, *args, **kwargs)
        if not check_user_access(user_id):
            update.message.reply_text(
                "You don't have access to this feature. Please subscribe first by using /start."
            )
            return
        return func(update, context, *args, **kwargs)

    return wrapped


def log_command_usage(func):
    @functools.wraps(func)
    def wrapper(update, context, *args, **kwargs):
        # Get the command name and user ID
        command_name = func.__name__
        user_id = update.effective_user.id

        # Log command usage to the database
        session = Session()
        command_usage = CommandUsage(user_id=user_id, command_name=command_name)
        session.add(command_usage)
        session.commit()

        # Call the original command handler function
        return func(update, context, *args, **kwargs)

    return wrapper
