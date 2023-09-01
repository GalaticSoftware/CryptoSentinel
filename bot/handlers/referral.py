from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext
from bot.database import Session, User, ReferralCodes, Referrals
from sqlalchemy.exc import NoResultFound
import logging

# setup logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


# Define constants
USED_REFERRAL_CODE_YES = "yes"
USED_REFERRAL_CODE_NO = "no"
REFERRAL_STATUS_ACTIVE = "active"
SUBSCRIPTION_TYPE_FREE_REFERRED = "free-referred"


class UseReferralHandler:
    @staticmethod
    def use_referral(update: Update, context: CallbackContext):
        user_id = update.effective_user.id
        username = update.effective_user.username

        logging.info(
            f"Processing referral for user: id={user_id}, username={username}")

        # Get the referral code from the command arguments
        referral_code = context.args[0] if context.args else None

        if not referral_code:
            logging.info("No referral code provided.")
            update.message.reply_text("Please provide a referral code.")
            return

        logging.info(f"Referral code provided: {referral_code}")

        session = Session()

        try:
            # Check if the referral code exists in the database
            referral = session.query(ReferralCodes).filter_by(
                code=referral_code).first()

            if not referral:
                logging.info(
                    f"Referral code not found in the database: {referral_code}")
                raise NoResultFound

            logging.info(
                f"Referral code found in the database: {referral_code}")

            # Check if the user exists in the database
            user = session.query(User).filter_by(telegram_id=user_id).first()
            if not user:
                logging.info(
                    f"User not found in the database: id={user_id}, username={username}")
                update.message.reply_text("User does not exist.")
                return

            if user.has_access:
                logging.info(
                    f"User already has access: id={user_id}, username={username}")
                update.message.reply_text(
                    "You already have access to premium features and can't use a referral code.")
                return

            logging.info(
                f"User found in the database: id={user.id}, telegram_id={user.telegram_id}, username={user.username}")

            # Check if the referrer exists in the database
            referrer = session.query(User).filter_by(
                id=referral.user_id).first()
            if not referrer:
                logging.info(
                    f"Referrer not found in the database: id={referral.user_id}")
                update.message.reply_text("Referrer does not exist.")
                return

            logging.info(
                f"Referrer found in the database: id={referrer.id}, telegram_id={referrer.telegram_id}, username={referrer.username}")

            # Check if the user has already used a referral code
            if user.used_referral_code == USED_REFERRAL_CODE_YES:
                logging.info(
                    f"User has already used a referral code: id={user.id}, username={user.username}")
                update.message.reply_text(
                    "You have already used a referral code.")
                return

            logging.info(
                f"User has not used a referral code: id={user.id}, username={user.username}")

            # Update the user's record with the referral code
            user.used_referral_code = USED_REFERRAL_CODE_YES
            user.referrer_id = referral.user_id
            user.has_access = True
            user.subscription_end = datetime.now() + timedelta(weeks=1)
            user.subscription_type = SUBSCRIPTION_TYPE_FREE_REFERRED

            logging.info(
                f"Updated user's record with referral code: id={user.id}, username={user.username}, referrer_id={user.referrer_id}, used_referral_code={user.used_referral_code}")

            # Add a new record to the Referrals table
            new_referral = Referrals(
                user_id=referral.user_id,
                referral_code=referral_code,
                referred_user_id=user_id,
                referred_user_username=username,
                status=REFERRAL_STATUS_ACTIVE
            )

            session.add(new_referral)
            logging.info(
                f"Added new referral to the database: user_id={new_referral.user_id}, referral_code={new_referral.referral_code}, referred_user_id={new_referral.referred_user_id}, referred_user_username={new_referral.referred_user_username}, status={new_referral.status}")

            # Commit the changes to the database
            session.commit()

            logging.info("Committed changes to the database.")

            update.message.reply_text(
                "Referral code accepted! You now have a free week of premium service.")

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            update.message.reply_text(
                "Invalid referral code. Please try again.")

        finally:
            session.close()
            logging.info("Database session closed.")
