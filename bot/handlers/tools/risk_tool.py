from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Define global states
CHOOSING, STOP_LOSS, TAKE_PROFIT, RISK_REWARD, POSITION_SIZE = range(5)


class RiskTool:
    def __init__(self):
        self.entry_price = None
        self.stop_loss_price = None
        self.take_profit_price = None

    @staticmethod
    def start(update: Update, context: CallbackContext) -> int:
        reply_keyboard = [['Stop Loss', 'Take Profit'], ['Risk/Reward', 'Position Size']]
        update.message.reply_text(
            'What do you want to calculate?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
        )
        return CHOOSING

    def stop_loss(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(
            'What is your entry price?',
            reply_markup=ReplyKeyboardRemove(),
        )
        return STOP_LOSS

    def take_profit(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(
            'What is your entry price?',
            reply_markup=ReplyKeyboardRemove(),
        )
        return TAKE_PROFIT

    def risk_reward(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(
            'What is your entry price?',
            reply_markup=ReplyKeyboardRemove(),
        )
        return RISK_REWARD

    def position_size(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text(
            'What is your account size?',
            reply_markup=ReplyKeyboardRemove(),
        )
        return POSITION_SIZE

    def calculate_stop_loss(self, update: Update, context: CallbackContext) -> int:
        self.entry_price = float(update.message.text)
        # Perform calculations for stop loss
        # ...
        update.message.reply_text(f"Your stop loss price is: {self.stop_loss_price}")
        return ConversationHandler.END

    def calculate_take_profit(self, update: Update, context: CallbackContext) -> int:
        self.entry_price = float(update.message.text)
        # Perform calculations for take profit
        # ...
        update.message.reply_text(f"Your take profit price is: {self.take_profit_price}")
        return ConversationHandler.END

    def calculate_risk_reward(self, update: Update, context: CallbackContext) -> int:
        self.entry_price = float(update.message.text)
        # Perform calculations for risk/reward
        # ...
        update.message.reply_text("Your risk/reward ratio is: ...")
        return ConversationHandler.END

    def calculate_position_size(self, update: Update, context: CallbackContext) -> int:
        self.account_size = float(update.message.text)
        # Perform calculations for position size
        # ...
        update.message.reply_text("Your position size is: ...")
        return ConversationHandler.END

    @staticmethod
    def done(update: Update, context: CallbackContext) -> int:
        user = update.message.from_user
        update.message.reply_text(
            f"Thank you for using the risk tool, {user.first_name}!"
            " I hope we can talk again some day.",
            reply_markup=ReplyKeyboardRemove(),
        )

        return ConversationHandler.END


