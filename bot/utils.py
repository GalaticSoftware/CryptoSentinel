from functools import wraps
from telegram import Update
from telegram.ext import CallbackContext
from users.management import check_user_access

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
