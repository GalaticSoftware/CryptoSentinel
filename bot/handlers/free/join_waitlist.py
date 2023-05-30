from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Session, User, WaitingList


class JoinWaitlistHandler:
    def join_waitlist(update: Update, context: CallbackContext):
        user_id = update.message.from_user.id
        username = update.message.from_user.username
        session = Session()

        # Check if the user is already in the waiting list
        user_in_waiting_list = (
            session.query(WaitingList).filter_by(telegram_id=user_id).first()
        )

        if user_in_waiting_list:
            update.message.reply_text(
                "You're already on the waiting list for the premium tier!"
            )
        else:
            # Add the user to the waiting list
            session.add(WaitingList(telegram_id=user_id, username=username))
            session.commit()
            update.message.reply_text(
                "You've been added to the waiting list for the premium tier! You'll receive a free one-month trial once it becomes available."
            )

        session.close()
