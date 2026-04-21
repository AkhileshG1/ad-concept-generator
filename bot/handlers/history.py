"""
bot/handlers/history.py — /history command to show last 5 generated ads.
"""
from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions


async def cmd_history(update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await show_history(update.message, context, user_id)


async def show_history(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = sessions.get(user_id)
    history = session.history

    if not history:
        await message.reply_text(
            "📭 No ads yet! Send /start to create your first one."
        )
        return

    text = "📚 *Your Last Ad History:*\n\n"
    for i, ad in enumerate(history, 1):
        product  = ad.get("product", "Unknown")
        headline = ad.get("headline", "—")
        platform = ad.get("platform", "—")
        text += (
            f"*#{i} — {product}*\n"
            f"📌 {headline}\n"
            f"📲 Platform: `{platform}`\n\n"
        )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Create a New Ad", callback_data="action:new_ad")]
    ])

    await message.reply_text(text.strip(), parse_mode="Markdown", reply_markup=keyboard)
