"""bot/handlers/generate.py — Ad copy generation + rating feedback loop."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.prompts import build_copy_prompt
from bot.gemini_client import generate_ad_copy
from bot.quality import copy_warnings
from config import State, FREE_ADS_PER_DAY


async def run_generate_copy(message: Message, context: ContextTypes.DEFAULT_TYPE,
                             user_id: int, feedback: str = ""):
    session = sessions.get(user_id)

    if not session.can_generate_ad():
        limit = FREE_ADS_PER_DAY if not session.is_pro else 999
        await message.reply_text(
            f"⚠️ Daily ad limit reached ({limit}/day on your plan).\n\n"
            "⭐ *Upgrade to PRO* for unlimited ads!\n/upgrade",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Upgrade Now", callback_data="buy:monthly")]
            ])
        )
        return

    prompt = build_copy_prompt(session, feedback=feedback, language=session.language_code)

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        copy = await loop.run_in_executor(
            None, generate_ad_copy, prompt, session.photos or None
        )
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower():
            await message.reply_text(
                "⏳ *AI is busy right now* — too many requests per minute.\n\n"
                "The bot tried 3 times automatically but the API is still throttled.\n"
                "Please wait **30 seconds** and try again.\n\n"
                "💡 _This is a free-tier rate limit (5 requests/minute), not a billing issue._",
                parse_mode="Markdown"
            )
        else:
            await message.reply_text(
                f"❌ *Generation error:* `{str(e)[:200]}`\n\n"
                "Try /start to begin again.",
                parse_mode="Markdown"
            )
        return

    session.current_copy = copy
    session.record_ad()
    session.state = State.AWAITING_RATING

    warn = copy_warnings(copy)
    text = _format_copy(copy) + (f"\n\n{warn}" if warn else "")
    await message.reply_text(text, parse_mode="Markdown", reply_markup=_rating_kb())


def _format_copy(copy: dict) -> str:
    tags = " ".join(f"#{t.lstrip('#')}" for t in copy.get("hashtags",[]))
    return (
        "✨ *Your Ad Copy:*\n\n"
        f"📌 *Headline:* {copy.get('headline','—')}\n\n"
        f"📝 *Body:*\n{copy.get('body','—')}\n\n"
        f"👉 *CTA:* {copy.get('cta','—')}\n\n"
        f"#️⃣ *Hashtags:* {tags or '—'}\n\n"
        f"🔀 *A/B Test:* _{copy.get('ab_variation','—')}_\n"
        f"🎯 *Audience:* _{copy.get('audience_description','—')}_\n\n"
        "━━━━━━━━━━━━━━\n*Rate this ad:*"
    )


def _rating_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⭐ {i}", callback_data=f"rate:{i}") for i in range(1,6)],
        [InlineKeyboardButton("✅ Looks great — make the image!", callback_data="rate:approve")],
    ])


async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = sessions.get(query.from_user.id)
    if session.state != State.AWAITING_RATING:
        return

    rating = query.data.split(":",1)[1]
    if rating in ("approve","4","5"):
        session.state = State.GENERATING_IMG
        photo_hint = " Using your real product photo! 🎨" if session.photos else ""
        await query.edit_message_text(
            f"🎨 Generating your professional ad poster...{photo_hint}\n"
            "_v2 compositor: background removal + pro layout — ~10 seconds_",
            parse_mode="Markdown"
        )
        from bot.handlers.image import run_generate_image
        await run_generate_image(query.message, context, query.from_user.id)
    else:
        session.feedback_count += 1
        if session.feedback_count >= 3:
            await query.edit_message_text("Tell me what you'd like changed (or /start to reset):")
        else:
            await query.edit_message_text(
                f"Rated {rating}/5. 📝\n\n*What should I change?*\n"
                "_E.g. 'Too formal', 'Focus on price', 'Make it shorter', 'Add more emotion'_",
                parse_mode="Markdown"
            )
        session.state = State.AWAITING_RATING


async def regenerate_with_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE, feedback: str):
    session = sessions.get(update.effective_user.id)
    await update.message.reply_text(
        f"🔄 Regenerating with feedback: _\"{feedback}\"_...", parse_mode="Markdown"
    )
    session.state = State.GENERATING_COPY
    await run_generate_copy(update.message, context, update.effective_user.id, feedback=feedback)
