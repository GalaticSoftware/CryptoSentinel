from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import CallbackContext, CallbackQueryHandler, PreCheckoutQueryHandler
from users.management import get_or_create_user, update_user_access, revoke_user_access
from config.settings import STRIPE_PROVIDER_TOKEN
from datetime import datetime, timedelta
import logging

# payment handler


class SubscribeHandler:
    # Define subscription plans
    subscription_plans = [
        {
            "label": "Monthly Subscription",
            "price": 1499,
            "duration": timedelta(days=30),
            "description": "Monthly Crypto Sentinel bot subscription",
        },
        {
            "label": "3_Monthly Subscription",
            "price": 3999,
            "duration": timedelta(days=90),
            "description": "3-Monthly Crypto Sentinel bot subscription",
        },
        {
            "label": "Yearly Subscription",
            "price": 14999,
            "duration": timedelta(days=365),
            "description": "Yearly Crypto Sentinel bot subscription",
        },
    ]

    def subscribe(update: Update, context: CallbackContext):
        query = update.callback_query
        query.answer()

        # Get the user's Telegram ID
        user_id = update.effective_user.id
        username = update.effective_user.username

        # Create or retrieve the user from the database
        user = get_or_create_user(user_id, username)

        # Create subscription buttons
        buttons = []
        for plan in SubscribeHandler.subscription_plans:
            button = InlineKeyboardButton(
                plan["label"],
                callback_data=f"subscribe_{plan['label'].lower().replace(' ', '_')}",
            )
            buttons.append(button)

        # Display subscription options
        keyboard = InlineKeyboardMarkup.from_column(buttons)
        update.effective_message.reply_text(
            "Please choose a subscription plan:", reply_markup=keyboard
        )

    def payment_received(update: Update, context: CallbackContext):
        query = update.pre_checkout_query
        query.answer(True)

        # Get the user's Telegram ID
        user_id = update.effective_user.id
        username = update.effective_user.username

        # Extract subscription type from payload
        subscription_type = query.invoice_payload.split("-")[-1]

        # Update the user's access status and subscription type in the database
        subscription_end = datetime.utcnow() + timedelta(
            days=3 * 30
        )  # For testing purposes, you can change this to the actual duration of the subscription
        update_user_access(
            user_id,
            has_access=True,
            subscription_end=subscription_end,
            subscription_type=subscription_type,
        )

        # Add logging
        logging.info(f"User {username} (ID: {user_id}) subscribed")

        # Confirm the payment
        context.bot.send_message(
            user_id, "Thank you for subscribing! You now have access to all features."
        )

    def revoke_access(context: CallbackContext):
        user_id = context.job.context
        revoke_user_access(user_id)

        # Add logging
        logging.info(f"User access revoked for user ID: {user_id}")

    subscribe_handler = CallbackQueryHandler(subscribe, pattern="^subscribe$")
    payment_handler = PreCheckoutQueryHandler(payment_received)

    # Subscription plan selection handlers
    monthly_subscription_handler = CallbackQueryHandler(
        lambda update, context: send_invoice(
            update, context, SubscribeHandler.subscription_plans[0]
        ),
        pattern="^subscribe_monthly_subscription$",
    )
    three_monthly_subscription_handler = CallbackQueryHandler(
        lambda update, context: send_invoice(
            update, context, SubscribeHandler.subscription_plans[1]
        ),
        pattern="^subscribe_3_monthly_subscription$",  # Update the pattern string here
    )
    yearly_subscription_handler = CallbackQueryHandler(
        lambda update, context: send_invoice(
            update, context, SubscribeHandler.subscription_plans[2]
        ),
        pattern="^subscribe_yearly_subscription$",
    )

    @staticmethod
    def send_invoice_monthly(update: Update, context: CallbackContext):
        send_invoice(update, context, SubscribeHandler.subscription_plans[0])

    @staticmethod
    def send_invoice_3_monthly(update: Update, context: CallbackContext):
        send_invoice(update, context, SubscribeHandler.subscription_plans[1])

    @staticmethod
    def send_invoice_yearly(update: Update, context: CallbackContext):
        send_invoice(update, context, SubscribeHandler.subscription_plans[2])


def send_invoice(update: Update, context: CallbackContext, plan):
    user_id = update.effective_user.id

    price = LabeledPrice(plan["label"], plan["price"])
    payload = f"{user_id}-subscription-{plan['label'].lower().replace('_', '_')}"
    start_parameter = f"{plan['label'].lower().replace(' ', '_')}-subscription"
    currency = "USD"

    context.bot.send_invoice(
        user_id,
        title=plan["label"],
        description=plan["description"],
        payload=payload,
        provider_token=STRIPE_PROVIDER_TOKEN,
        start_parameter=start_parameter,
        currency=currency,
        prices=[price],
    )
