"""bot/handlers/start.py — /start with PRO-aware platform selector."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from config import State, BUSINESS_TYPES, PLATFORMS_FREE, PLATFORMS_PRO, ALL_PLATFORMS


WELCOME = (
    "👋 *Welcome to AdBot!*\n\n"
    "I generate complete, professional ads for your business in under 2 minutes.\n"
    "✅ Ad copy · ✅ Poster image · ✅ Hashtags · ✅ WhatsApp & Instagram ready\n\n"
    "🆓 *Free:* 3 ads/day · Instagram + WhatsApp\n"
    "⭐ *PRO:* Unlimited · All platforms · Google Ads · Print Poster\n\n"
    "Let's start — what type of business? 👇"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = sessions.get(user.id)
    session.reset_for_new_ad()
    session.state = State.CHOOSE_BUSINESS

    # v2: capture user's language from Telegram profile
    try:
        from bot.language import extract_language_from_update
        session.language_code = extract_language_from_update(update)
    except Exception:
        session.language_code = "en"

    keyboard = [[InlineKeyboardButton(l, callback_data=f"btype:{v}")] for l, v in BUSINESS_TYPES.items()]
    await update.message.reply_text(WELCOME, parse_mode="Markdown",
                                    reply_markup=InlineKeyboardMarkup(keyboard))



async def handle_business_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = sessions.get(query.from_user.id)
    if session.state != State.CHOOSE_BUSINESS:
        return
    session.business_type = query.data.split(":",1)[1]
    session.state = State.CHOOSE_PLATFORM

    session.check_pro_expiry()
    label = next(k for k,v in BUSINESS_TYPES.items() if v == session.business_type)

    # PRO users see all platforms; free users see locked ones
    if session.is_pro:
        rows = [[InlineKeyboardButton(l, callback_data=f"platform:{v}")] for l,v in ALL_PLATFORMS.items()]
    else:
        rows = (
            [[InlineKeyboardButton(l, callback_data=f"platform:{v}")] for l,v in PLATFORMS_FREE.items()]
            + [[InlineKeyboardButton(f"🔒 {l} — PRO only", callback_data="platform:upgrade")] for l,v in PLATFORMS_PRO.items()]
        )

    await query.edit_message_text(
        f"✅ *{label}*\n\nWhere do you want to run this ad?",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(rows)
    )


async def handle_platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = sessions.get(query.from_user.id)

    platform = query.data.split(":",1)[1]

    if platform == "upgrade":
        await query.message.reply_text(
            "⭐ *This platform format is PRO only.*\n\n"
            "Upgrade to unlock Google Ads, Print Poster, and the Full Ad Pack!\n"
            "Use /upgrade to see plans.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Upgrade to PRO", callback_data="buy:monthly")]
            ])
        )
        return

    session.platform = platform
    session.state = State.GET_PRODUCT
    label = next((k for k,v in ALL_PLATFORMS.items() if v == platform), platform)

    await query.edit_message_text(
        f"📲 *{label}* selected!\n\n*What's your product or service name?*\n"
        "_E.g. 'Mango Lassi', 'Web Design Package', 'Handmade Candles'_",
        parse_mode="Markdown"
    )
