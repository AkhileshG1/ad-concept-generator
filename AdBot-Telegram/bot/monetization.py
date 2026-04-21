"""
bot/monetization.py — Telegram Stars payment flow for PRO upgrades.

Revenue model:
  50 Stars  (~$0.65) → 7 days PRO
  150 Stars (~$1.95) → 30 days PRO
  500 Stars (~$6.50) → 90 days PRO  ← best value, push this one

Passive income:
  Canva affiliate links embedded in every ad delivery (25-80% commission)

Stars → Cash:
  Withdraw via BotFather → Fragment → convert to TON → sell for cash
"""
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    LabeledPrice,
)
from telegram.ext import ContextTypes

from bot.session import sessions
from config import STARS_WEEKLY, STARS_MONTHLY, STARS_QUARTERLY


PRO_PLANS = {
    "weekly":    (STARS_WEEKLY,    7,  "7-Day PRO",   "🚀 7 days of unlimited ads & images"),
    "monthly":   (STARS_MONTHLY,  30,  "30-Day PRO",  "⭐ 30 days of unlimited ads & images"),
    "quarterly": (STARS_QUARTERLY, 90, "90-Day PRO",  "👑 Best value — 90 days PRO access"),
}


async def cmd_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the upgrade menu."""
    session = sessions.get(update.effective_user.id)

    if session.is_pro:
        days = session.pro_days_remaining()
        await update.message.reply_text(
            f"⭐ You're already *PRO* — {days} day(s) remaining!\n\n"
            "Use /upgrade to stack more time on top.",
            parse_mode="Markdown",
            reply_markup=_upgrade_keyboard(),
        )
        return

    text = (
        "🆓 *Free Tier*: 3 ads/day · 2 images/day · Instagram + WhatsApp only\n\n"
        "⭐ *PRO Tier* unlocks:\n"
        "  ✅ Unlimited ads per day\n"
        "  ✅ 10 images per day\n"
        "  ✅ Google Ad + Print Poster formats\n"
        "  ✅ Full Ad Pack (all 4 platforms at once)\n"
        "  ✅ Priority generation\n\n"
        "Pay natively in Telegram — no card needed 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=_upgrade_keyboard())


def _upgrade_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔥 7 days — {STARS_WEEKLY} ⭐", callback_data="buy:weekly")],
        [InlineKeyboardButton(f"💎 30 days — {STARS_MONTHLY} ⭐", callback_data="buy:monthly")],
        [InlineKeyboardButton(f"👑 90 days — {STARS_QUARTERLY} ⭐ (Best!)", callback_data="buy:quarterly")],
        [InlineKeyboardButton("ℹ️ What is Telegram Stars?", callback_data="buy:info")],
    ])


async def handle_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle buy button clicks — send Telegram Stars invoice."""
    query = update.callback_query
    await query.answer()

    plan_key = query.data.split(":", 1)[1]

    if plan_key == "info":
        await query.message.reply_text(
            "ℹ️ *Telegram Stars* are the native payment method inside Telegram.\n\n"
            "You can buy Stars directly in the Telegram app:\n"
            "  • iOS: via App Store\n"
            "  • Android: via Google Play\n"
            "  • Desktop: via in-app purchase\n\n"
            "No credit card or bank details shared with this bot — 100% secure.",
            parse_mode="Markdown",
        )
        return

    if plan_key not in PRO_PLANS:
        return

    stars, days, title, description = PRO_PLANS[plan_key]

    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title=f"AdBot {title}",
        description=description,
        payload=f"pro_{plan_key}_{query.from_user.id}",
        provider_token="",          # Empty string = Telegram Stars
        currency="XTR",             # XTR = Telegram Stars
        prices=[LabeledPrice(label=title, amount=stars)],
    )


async def handle_pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Always approve — validation happens on successful payment."""
    await update.pre_checkout_query.answer(ok=True)


async def handle_successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activate PRO when Stars payment is confirmed."""
    payment = update.message.successful_payment
    payload = payment.invoice_payload          # e.g. "pro_monthly_12345"

    parts    = payload.split("_")
    plan_key = parts[1]                        # weekly / monthly / quarterly
    user_id  = update.effective_user.id

    if plan_key not in PRO_PLANS:
        return

    stars, days, title, _ = PRO_PLANS[plan_key]

    session = sessions.get(user_id)
    session.activate_pro(days)

    await update.message.reply_text(
        f"🎉 *Payment confirmed!* Welcome to AdBot PRO!\n\n"
        f"✅ *{title}* activated — {days} days of unlimited ads.\n"
        f"💡 Your PRO access stacks if you upgrade again before expiry.\n\n"
        f"Send /start to create your next unlimited ad!",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current plan + usage stats."""
    user_id = update.effective_user.id
    session = sessions.get(user_id)
    session.check_pro_expiry()

    if session.is_pro:
        days = session.pro_days_remaining()
        plan = f"⭐ *PRO* — {days} day(s) remaining"
        limits = f"Unlimited ads · 10 images/day"
    else:
        plan = "🆓 *Free*"
        limits = f"{session.ads_remaining()} ads remaining today · {session.images_today}/{2} images used"

    await update.message.reply_text(
        f"📊 *Your AdBot Status*\n\n"
        f"Plan: {plan}\n"
        f"Usage: {limits}\n"
        f"Ads created: {len(session.history)} (stored)\n\n"
        f"{'Upgrade with /upgrade to unlock more!' if not session.is_pro else 'Thank you for being PRO! 🙏'}",
        parse_mode="Markdown",
        reply_markup=None if session.is_pro else InlineKeyboardMarkup([
            [InlineKeyboardButton("⭐ Upgrade to PRO", callback_data="buy:monthly")]
        ]),
    )
