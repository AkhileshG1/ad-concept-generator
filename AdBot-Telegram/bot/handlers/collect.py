"""bot/handlers/collect.py — Step-by-step product info collection."""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from config import State


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = sessions.get(update.effective_user.id)
    text = update.message.text.strip()

    if session.state == State.GET_PRODUCT:
        session.product_name = text
        session.state = State.GET_USP
        await update.message.reply_text(
            f"✅ *{text}*\n\n"
            "What makes it special? Write your *USP* in 1-2 sentences.\n"
            "_E.g. 'Made with organic ingredients, no preservatives, delivered fresh daily'_",
            parse_mode="Markdown"
        )

    elif session.state == State.GET_USP:
        session.usp = text
        session.state = State.GET_AUDIENCE
        await update.message.reply_text(
            "🎯 Got it!\n\n*Who is your target audience?*\n"
            "_E.g. 'Health-conscious parents aged 28-45' or 'College students in Mumbai'_",
            parse_mode="Markdown"
        )

    elif session.state == State.GET_AUDIENCE:
        session.audience = text
        session.state = State.WAITING_PHOTO
        await update.message.reply_text(
            "🚀 Almost done!\n\nDo you have *product photos* to upload?\n"
            "_(Photos help generate a more accurate poster image)_",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Yes — upload photos", callback_data="photo:yes")],
                [InlineKeyboardButton("⚡ Skip — generate now!", callback_data="photo:no")],
            ])
        )

    elif session.state == State.AWAITING_RATING:
        from bot.handlers.generate import regenerate_with_feedback
        await regenerate_with_feedback(update, context, text)

    elif session.state == State.IDLE:
        await update.message.reply_text("Send /start to create a new ad.")

    else:
        await update.message.reply_text("Follow the prompts above, or /start to restart.")


async def handle_photo_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = sessions.get(query.from_user.id)
    choice = query.data.split(":",1)[1]

    if choice == "no":
        session.state = State.GENERATING_COPY
        await query.edit_message_text("⚡ Generating your ad now... _(~10 seconds)_", parse_mode="Markdown")
        from bot.handlers.generate import run_generate_copy
        await run_generate_copy(query.message, context, query.from_user.id)

    elif choice == "yes":
        await query.edit_message_text(
            "📸 *Send your product photos* (up to 3, one by one).\n\nWhen done, tap the button:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Done — Generate my ad!", callback_data="photo:done")]
            ])
        )


async def handle_photo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = sessions.get(update.effective_user.id)
    if session.state != State.WAITING_PHOTO:
        return
    if len(session.photos) >= 3:
        await update.message.reply_text("ℹ️ Already have 3 photos — tap *Done* above!", parse_mode="Markdown")
        return
    file = await context.bot.get_file(update.message.photo[-1].file_id)
    session.photos.append(bytes(await file.download_as_bytearray()))
    count = len(session.photos)
    await update.message.reply_text(
        f"✅ Photo {count} received!" +
        (f" Send up to {3-count} more, or tap *Done*." if count < 3 else " That's the max — tap *Done* above!"),
        parse_mode="Markdown"
    )


async def handle_photo_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    session = sessions.get(query.from_user.id)
    session.state = State.GENERATING_COPY
    await query.edit_message_text(
        f"📸 {len(session.photos)} photo(s) received! Generating now... _(~15 seconds)_",
        parse_mode="Markdown"
    )
    from bot.handlers.generate import run_generate_copy
    await run_generate_copy(query.message, context, query.from_user.id)
