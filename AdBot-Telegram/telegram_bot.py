"""
telegram_bot.py — AdBot entry point.

Commands:
  /start    → Create a new ad
  /upgrade  → See PRO plans (Telegram Stars)
  /status   → View your plan + usage
  /history  → Last 5 ads
  /help     → Help message
"""
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, PreCheckoutQueryHandler, filters,
)

from config import TELEGRAM_TOKEN
from bot.handlers.start   import cmd_start, handle_business_choice, handle_platform_choice
from bot.handlers.collect import handle_text, handle_photo_option, handle_photo_upload, handle_photo_done
from bot.handlers.generate import handle_rating
from bot.handlers.deliver  import handle_action
from bot.handlers.history  import cmd_history
from bot.monetization import (
    cmd_upgrade, handle_buy_callback, handle_pre_checkout,
    handle_successful_payment, cmd_status,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)


async def cmd_help(update, context):
    await update.message.reply_text(
        "🤖 *AdBot Commands:*\n\n"
        "/start    — Create a new ad\n"
        "/upgrade  — Upgrade to PRO (⭐ Telegram Stars)\n"
        "/status   — View your plan & daily usage\n"
        "/history  — Your last 5 ads\n"
        "/help     — This message\n\n"
        "🆓 *Free:* 3 ads/day · 2 images/day · Instagram + WhatsApp\n"
        "⭐ *PRO:* Unlimited · All platforms · Google Ads · Print Poster\n\n"
        "💡 *Tips:*\n"
        "• Upload up to 3 product photos for better images\n"
        "• Rate 1-3 to regenerate with your feedback\n"
        "• Canva button opens a template pre-matched to your ad type\n"
        "• Pollinations.ai images work globally — no region blocks",
        parse_mode="Markdown",
    )


def main():
    if not TELEGRAM_TOKEN:
        raise ValueError(
            "\n\n❌ TELEGRAM_BOT_TOKEN not set!\n"
            "1. Go to https://t.me/BotFather → /newbot → copy token\n"
            "2. Add to .env: TELEGRAM_BOT_TOKEN=your_token_here\n"
        )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("upgrade", cmd_upgrade))
    app.add_handler(CommandHandler("status",  cmd_status))

    # ── Onboarding keyboards ──────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_business_choice, pattern=r"^btype:"))
    app.add_handler(CallbackQueryHandler(handle_platform_choice, pattern=r"^platform:"))

    # ── Photo flow ────────────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_photo_option, pattern=r"^photo:(yes|no)$"))
    app.add_handler(CallbackQueryHandler(handle_photo_done,   pattern=r"^photo:done$"))

    # ── Rating + delivery actions ─────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_rating, pattern=r"^rate:"))
    app.add_handler(CallbackQueryHandler(handle_action, pattern=r"^action:"))

    # ── Monetization (Telegram Stars) ─────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_buy_callback,  pattern=r"^buy:"))
    app.add_handler(PreCheckoutQueryHandler(handle_pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, handle_successful_payment))

    # ── Message handlers ──────────────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_upload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    log.info("🤖 AdBot is live — Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
