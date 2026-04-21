"""
telegram_bot.py — Main entry point for the AI Ad Telegram Bot.

Registers all handlers and runs via long-polling (webhook-ready:
just point your webhook URL here and swap `run_polling` → `run_webhook`).
"""
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_TOKEN
from bot.handlers.start import cmd_start, handle_business_choice, handle_platform_choice
from bot.handlers.collect import (
    handle_text_input, handle_photo_option, handle_photo_upload, handle_photo_done,
)
from bot.handlers.generate import handle_rating, regenerate_with_feedback
from bot.handlers.deliver import handle_action
from bot.handlers.history import cmd_history

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def cmd_help(update, context):
    await update.message.reply_text(
        "🤖 *AdBot Commands:*\n\n"
        "/start — Create a new ad\n"
        "/history — View your last 5 ads\n"
        "/help — Show this message\n\n"
        "💡 *Tips:*\n"
        "• Upload up to 3 product photos for better image generation\n"
        "• Rate ads 1-3 to regenerate with feedback (up to 3 attempts)\n"
        "• 'Full Ad Pack' generates Instagram + WhatsApp + Google + Poster formats\n"
        "• Daily limits: 10 ads / 5 images (free tier)",
        parse_mode="Markdown",
    )


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Add it to your .env file: TELEGRAM_BOT_TOKEN=your_token_here"
        )

    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))

    # ── Inline keyboard callbacks ─────────────────────────────────────────────
    # Business type selection
    app.add_handler(CallbackQueryHandler(handle_business_choice, pattern=r"^btype:"))
    # Platform selection
    app.add_handler(CallbackQueryHandler(handle_platform_choice, pattern=r"^platform:"))
    # Photo yes/no/done
    app.add_handler(CallbackQueryHandler(handle_photo_option, pattern=r"^photo:(yes|no)$"))
    app.add_handler(CallbackQueryHandler(handle_photo_done,   pattern=r"^photo:done$"))
    # Rating
    app.add_handler(CallbackQueryHandler(handle_rating, pattern=r"^rate:"))
    # Post-delivery actions
    app.add_handler(CallbackQueryHandler(handle_action, pattern=r"^action:"))

    # ── Message handlers ──────────────────────────────────────────────────────
    # Photo uploads
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_upload))
    # All text (routes by state)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("🤖 AdBot is running — press Ctrl+C to stop")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,       # ignore stale messages from downtime
    )


if __name__ == "__main__":
    main()
