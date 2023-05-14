from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import CallbackContext, CallbackQueryHandler, PreCheckoutQueryHandler
from users.management import get_or_create_user, update_user_access, revoke_user_access
from config.settings import STRIPE_PROVIDER_TOKEN, STRIPE_PROVIDER_TOKEN_TEST
from datetime import datetime, timedelta
import datetime
import logging

# payment handler

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
        price = LabeledPrice('Premium Subscription', 3999)  # Price in the smallest currency unit (e.g., cents)
        payload = f"{user_id}-premium-subscription"
        start_parameter = 'premium-subscription'
        currency = 'USD'

        context.bot.send_invoice(
            user_id,
            title='Premium Subscription',
            description='Premium Crypto Sentinel bot subscription for 3 months',
            payload=payload,
            provider_token=STRIPE_PROVIDER_TOKEN_TEST,
            start_parameter=start_parameter,
            currency=currency,
            prices=[price]
        )

    def payment_received(update: Update, context: CallbackContext):
        query = update.pre_checkout_query
        query.answer(True)

        # Get the user's Telegram ID
        user_id = update.effective_user.id
        username = update.effective_user.username

        # # Update the user's access status in the database to True and use UTC time for consistency
        subscription_end = datetime.datetime.utcnow() + datetime.timedelta(minutes=10) # 10 minutes for testing and 3 months for production
        update_user_access(user_id, has_access=True, subscription_end=subscription_end)


        # now_utc = datetime.utcnow()
        # subscription_end = now_utc + timedelta(minutes=10) # 10 minutes for testing
        # update_user_access(user_id, has_access=True, subscription_end=subscription_end)

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

