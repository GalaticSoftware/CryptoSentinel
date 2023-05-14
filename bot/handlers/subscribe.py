from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from users.management import get_or_create_user, update_user_access, revoke_user_access
from config.settings import STRIPE_PROVIDER_TOKEN
import datetime
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

        # Create an invoice
        price = {'label': 'Bot Subscription', 'amount': 999}  # Price in the smallest currency unit (e.g., cents)
        payload = f"{user_id}-bot-subscription"
        start_parameter = 'bot-subscription'
        currency = 'USD'

        context.bot.send_invoice(
            user_id,
            title='Bot Subscription',
            description='Telegram bot subscription for 3 months',
            payload=payload,
            provider_token=STRIPE_PROVIDER_TOKEN,
            start_parameter=start_parameter,
            currency=currency,
            prices=[price]
        )

    def payment_received(update: Update, context: CallbackContext):
        query = update.pre_checkout_query
        query.answer()

        # Get the user's Telegram ID
        user_id = update.effective_user.id
        username = update.effective_user.username

        # Update the user's access status in the database
        update_user_access(user_id, has_access=True)

        # Schedule the access revocation after 3 months
        revoke_date = datetime.datetime.now() + datetime.timedelta(days=90)
        context.job_queue.run_once(revoke_user_access, revoke_date, context=user_id)

        # Add logging
        logging.info(f"User {username} (ID: {user_id}) subscribed")

        # Confirm the payment
        context.bot.send_message(user_id, "Thank you for subscribing! You now have access to all features for 3 months.")

    def revoke_access(context: CallbackContext):
        user_id = context.job.context
        revoke_user_access(user_id)

        # Add logging
        logging.info(f"User access revoked for user ID: {user_id}")

    subscribe_handler = CallbackQueryHandler(subscribe, pattern="^subscribe$")
    payment_handler = CallbackQueryHandler(payment_received, pattern="^pre_checkout_query$")
