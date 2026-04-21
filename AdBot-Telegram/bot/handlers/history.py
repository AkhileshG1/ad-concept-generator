"""bot/handlers/history.py — /history command."""
from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions


async def cmd_history(update, context: ContextTypes.DEFAULT_TYPE):
    await show_history(update.message, context, update.effective_user.id)


async def show_history(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = sessions.get(user_id)
    if not session.history:
        await message.reply_text("📭 No ads yet! Send /start to create your first one.")
        return
    text = "📚 *Your Recent Ads:*\n\n"
    for i, ad in enumerate(session.history, 1):
        text += f"*#{i} — {ad.get('product','?')}*\n📌 {ad.get('headline','—')}\n📲 `{ad.get('platform','—')}`\n\n"
    await message.reply_text(text.strip(), parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ New Ad", callback_data="action:new_ad")]
        ])
    )
