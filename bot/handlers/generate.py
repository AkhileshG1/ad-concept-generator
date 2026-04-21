"""
bot/handlers/generate.py — Ad copy generation + feedback/regeneration loop.

Flow:
  run_generate_copy → show copy → rating keyboard
  Rating 1-3 → ask for feedback text → regenerate_with_feedback
  Rating 4-5 → proceed to image generation
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.prompts import build_copy_prompt
from bot.gemini_client import generate_ad_copy
from bot.quality import describe_quality_issue
from config import State


async def run_generate_copy(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int, feedback: str = ""):
    """Core copy generation. Called by collect.py and by this module on re-gen."""
    session = sessions.get(user_id)

    # Rate limit check
    if not session.can_generate_ad():
        await message.reply_text(
            "⚠️ You've hit your daily ad limit (10 ads/day). Come back tomorrow or try /help!"
        )
        return

    prompt = build_copy_prompt(session, feedback=feedback)

    try:
        copy = await context.application.loop.run_in_executor(
            None, generate_ad_copy, prompt, session.photos or None
        )
    except Exception as e:
        await message.reply_text(
            f"❌ Oops — Gemini hit an error: `{e}`\n\nTry /start to begin again.",
            parse_mode="Markdown",
        )
        return

    session.current_copy = copy
    session.record_ad()
    session.state = State.AWAITING_RATING

    # Quality check on copy
    issue = describe_quality_issue(copy)

    text = _format_copy_display(copy, session.platform)
    if issue:
        text += f"\n\n{issue}"

    await message.reply_text(text, parse_mode="Markdown", reply_markup=_rating_keyboard())


def _format_copy_display(copy: dict, platform: str) -> str:
    headline = copy.get("headline", "—")
    body     = copy.get("body", "—")
    cta      = copy.get("cta", "—")
    hashtags = copy.get("hashtags", [])
    ab       = copy.get("ab_variation", "")
    audience = copy.get("audience_description", "")

    tag_str = " ".join(f"#{t.lstrip('#')}" for t in hashtags) if hashtags else "—"

    text = (
        "✨ *Here's your ad copy:*\n\n"
        f"📌 *Headline:* {headline}\n\n"
        f"📝 *Body:*\n{body}\n\n"
        f"👉 *CTA:* {cta}\n\n"
        f"#️⃣ *Hashtags:* {tag_str}"
    )

    if ab:
        text += f"\n\n🔀 *A/B Test Headline:* _{ab}_"
    if audience:
        text += f"\n\n🎯 *Ideal Audience:* _{audience}_"

    text += "\n\n━━━━━━━━━━━━━━━━━━━\n*Rate this ad (1–5):*"
    return text


def _rating_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ 1", callback_data="rate:1"),
            InlineKeyboardButton("⭐ 2", callback_data="rate:2"),
            InlineKeyboardButton("⭐ 3", callback_data="rate:3"),
            InlineKeyboardButton("⭐ 4", callback_data="rate:4"),
            InlineKeyboardButton("⭐ 5", callback_data="rate:5"),
        ],
        [InlineKeyboardButton("✅ Looks good — generate image!", callback_data="rate:approve")],
    ])


async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rating button clicks."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = sessions.get(user_id)

    if session.state != State.AWAITING_RATING:
        return

    rating = query.data.split(":", 1)[1]

    if rating == "approve" or rating in ("4", "5"):
        # Approved — move to image generation
        session.state = State.GENERATING_IMG
        await query.edit_message_text(
            "🎉 Great — generating your poster image now!\n"
            "_This takes about 10–20 seconds..._",
            parse_mode="Markdown",
        )
        from bot.handlers.image import run_generate_image
        await run_generate_image(query.message, context, user_id)

    else:
        # Low rating — ask for feedback
        session.feedback_count += 1
        if session.feedback_count >= 3:
            await query.edit_message_text(
                "🤔 Let's try a completely different angle. Tell me what you'd like changed "
                "(or send /start to reset):"
            )
        else:
            await query.edit_message_text(
                f"Got it — you rated it {rating}/5. 📝\n\n"
                "*What would you like changed?*\n"
                "_E.g. 'Make it more fun', 'Too formal', 'Focus on the price', 'Shorter body'_",
                parse_mode="Markdown",
            )
        session.state = State.AWAITING_RATING   # stays here, waiting for text feedback


async def regenerate_with_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE, feedback: str):
    """Called when user types feedback text while in AWAITING_RATING state."""
    user_id = update.effective_user.id
    session = sessions.get(user_id)

    await update.message.reply_text(
        f"🔄 Regenerating with your feedback: _\"{feedback}\"_...",
        parse_mode="Markdown",
    )
    session.state = State.GENERATING_COPY
    await run_generate_copy(update.message, context, user_id, feedback=feedback)
