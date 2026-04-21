"""
bot/handlers/collect.py — Collects product name, details, USP, audience, photos.

The state machine drives this step-by-step:
  GET_PRODUCT → GET_USP → GET_AUDIENCE → WAITING_PHOTO → (generate)
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from config import State


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Routes text messages through the collection states."""
    user_id = update.effective_user.id
    session = sessions.get(user_id)
    text = update.message.text.strip()

    if session.state == State.GET_PRODUCT:
        session.product_name = text
        session.state = State.GET_USP
        await update.message.reply_text(
            f"✅ *{text}* — love it!\n\n"
            "Now, what makes it special? Write 1-2 sentences about your *USP* "
            "(Unique Selling Proposition). What makes you different from competitors?\n\n"
            "_Example: 'Made with organic ingredients, no preservatives, delivered fresh daily'_",
            parse_mode="Markdown",
        )

    elif session.state == State.GET_USP:
        session.usp = text
        session.state = State.GET_AUDIENCE
        await update.message.reply_text(
            "Got it! 🎯\n\n"
            "Who is your *target audience*? Describe them briefly.\n\n"
            "_Example: 'Health-conscious parents aged 28-45' or 'College students in Mumbai'_",
            parse_mode="Markdown",
        )

    elif session.state == State.GET_AUDIENCE:
        session.audience = text
        session.state = State.WAITING_PHOTO
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📸 Yes, I'll upload photos", callback_data="photo:yes")],
            [InlineKeyboardButton("⚡ Skip — generate now!", callback_data="photo:no")],
        ])
        await update.message.reply_text(
            "Almost there! 🚀\n\n"
            "Do you have product photos to share? "
            "Uploading them helps me make the image more accurate.\n"
            "_(Up to 3 photos — send them one by one)_",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    elif session.state == State.IDLE:
        await update.message.reply_text(
            "Send /start to create a new ad, or /help for available commands."
        )

    elif session.state in (State.AWAITING_RATING,):
        # User typed text instead of clicking rating — handle as feedback
        from bot.handlers.generate import regenerate_with_feedback
        await regenerate_with_feedback(update, context, feedback=text)

    else:
        await update.message.reply_text("Please follow the prompts above, or send /start to restart.")


async def handle_photo_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the Yes/No photo upload choice."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = sessions.get(user_id)

    choice = query.data.split(":", 1)[1]

    if choice == "no":
        session.state = State.GENERATING_COPY
        await query.edit_message_text("⚡ Got it — generating your ad now...")
        from bot.handlers.generate import run_generate_copy
        await run_generate_copy(query.message, context, user_id)

    elif choice == "yes":
        await query.edit_message_text(
            "📸 *Send your product photos now* (up to 3).\n\n"
            "When you're done, tap the button below to generate your ad.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Done — Generate my ad!", callback_data="photo:done")]
            ]),
        )


async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receives photo uploads and stores them in the session."""
    user_id = update.effective_user.id
    session = sessions.get(user_id)

    if session.state != State.WAITING_PHOTO:
        return

    photo = update.message.photo[-1]      # highest resolution variant
    if len(session.photos) >= 3:
        await update.message.reply_text("ℹ️ I already have 3 photos — that's enough!")
        return

    file = await context.bot.get_file(photo.file_id)
    photo_bytes = await file.download_as_bytearray()
    session.photos.append(bytes(photo_bytes))

    count = len(session.photos)
    remaining = 3 - count
    await update.message.reply_text(
        f"✅ Photo {count} received!"
        + (f" Send up to {remaining} more, or tap *Done* above." if remaining else " That's the max — tap *Done* above!"),
        parse_mode="Markdown",
    )


async def handle_photo_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User tapped 'Done' after uploading photos."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = sessions.get(user_id)
    session.state = State.GENERATING_COPY

    photo_count = len(session.photos)
    await query.edit_message_text(
        f"📸 {photo_count} photo(s) received! Generating your ad now...\n_This takes about 10–15 seconds._",
        parse_mode="Markdown",
    )

    from bot.handlers.generate import run_generate_copy
    await run_generate_copy(query.message, context, user_id)
