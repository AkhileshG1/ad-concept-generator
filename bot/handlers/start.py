"""
bot/handlers/start.py — /start command and onboarding keyboards.

Flow:
  /start → business type selector → platform selector → product collection
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from config import State, BUSINESS_TYPES, PLATFORMS


WELCOME_MSG = (
    "👋 *Welcome to AdBot — your AI-powered ad creator!*\n\n"
    "I'll generate a complete, professional ad for your product in under 2 minutes "
    "— copy, image, hashtags, platform-ready formats, all free.\n\n"
    "Let's start with your business type 👇"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = sessions.get(user_id)
    session.reset_for_new_ad()
    session.state = State.CHOOSE_BUSINESS

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"btype:{key}")]
        for label, key in BUSINESS_TYPES.items()
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(WELCOME_MSG, parse_mode="Markdown", reply_markup=markup)


async def handle_business_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = sessions.get(user_id)

    if session.state != State.CHOOSE_BUSINESS:
        await query.answer("Please start a new ad with /start", show_alert=True)
        return

    btype = query.data.split(":", 1)[1]
    session.business_type = btype
    session.state = State.CHOOSE_PLATFORM

    label = next(k for k, v in BUSINESS_TYPES.items() if v == btype)
    await query.edit_message_text(
        f"Great — *{label}* it is! ✅\n\nNow, where do you want to run this ad?",
        parse_mode="Markdown",
        reply_markup=_platform_keyboard(),
    )


async def handle_platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = sessions.get(user_id)

    if session.state != State.CHOOSE_PLATFORM:
        await query.answer("Please start a new ad with /start", show_alert=True)
        return

    platform = query.data.split(":", 1)[1]
    session.platform = platform
    session.state = State.GET_PRODUCT

    label = next(k for k, v in PLATFORMS.items() if v == platform)
    await query.edit_message_text(
        f"Perfect — *{label}* 📲\n\n"
        "Now tell me about your product.\n\n"
        "*What's the product or service name?* (e.g. 'Mango Lassi', 'Web Design Service')",
        parse_mode="Markdown",
    )


def _platform_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"platform:{key}")]
        for label, key in PLATFORMS.items()
    ]
    return InlineKeyboardMarkup(keyboard)
