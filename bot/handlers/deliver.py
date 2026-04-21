"""
bot/handlers/deliver.py — The grand finale: deliver the complete Ad Pack.

Sends:
  • Ad image (via URL or bytes)
  • Full copy summary
  • Platform-specific formatted versions (if "all" selected)
  • Hashtag sets
  • WhatsApp share link
  • Canva template link
  • Another ad? keyboard
"""
import io
from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.links import (
    get_canva_link, get_whatsapp_share_link, get_instagram_caption,
    get_whatsapp_message, format_google_ad, format_poster_copy,
)
from bot.quality import describe_quality_issue
from config import State


async def deliver_full_pack(
    message: Message,
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    img_url: str | None = None,
    img_bytes: bytes | None = None,
):
    session = sessions.get(user_id)
    copy = session.current_copy

    # 1. Send image (URL or bytes)
    try:
        if img_url:
            await context.bot.send_photo(
                chat_id=message.chat_id,
                photo=img_url,
                caption="🖼️ *Your AI-generated poster!*",
                parse_mode="Markdown",
            )
        elif img_bytes:
            await context.bot.send_photo(
                chat_id=message.chat_id,
                photo=io.BytesIO(img_bytes),
                caption="🖼️ *Your AI-generated poster!*",
                parse_mode="Markdown",
            )
    except Exception:
        await message.reply_text("⚠️ Image could not be delivered — see Canva link below to create one.")

    # 2. Build the main copy summary
    ig_caption   = get_instagram_caption(copy)
    wa_message   = get_whatsapp_message(copy)
    wa_link      = get_whatsapp_share_link(wa_message)
    canva_link   = get_canva_link(session.business_type, session.platform)
    google_block = format_google_ad(copy)
    poster_block = format_poster_copy(copy)

    # 3. Main copy message
    main_text = (
        "🎁 *Your Complete Ad Pack is Ready!*\n\n"
        "━━━━━━━━━━━━━━\n"
        "📸 *Instagram Caption:*\n"
        f"{ig_caption}\n\n"
        "━━━━━━━━━━━━━━\n"
        "💬 *WhatsApp Message:*\n"
        f"{wa_message}\n\n"
    )

    if google_block:
        main_text += f"━━━━━━━━━━━━━━\n{google_block}\n\n"
    if poster_block:
        main_text += f"━━━━━━━━━━━━━━\n{poster_block}\n\n"

    main_text += (
        "━━━━━━━━━━━━━━\n"
        f"🔀 *A/B Test Headline:* _{copy.get('ab_variation','—')}_\n"
        f"🎯 *Ideal Audience:* _{copy.get('audience_description','—')}_"
    )

    # Telegram message limit ~4096 chars — split if needed
    await _send_long_message(message, main_text, parse_mode="Markdown")

    # 4. Action buttons
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Share on WhatsApp", url=wa_link)],
        [InlineKeyboardButton("🎨 Open Canva Template", url=canva_link)],
        [InlineKeyboardButton("🔁 Create Another Ad", callback_data="action:new_ad")],
        [InlineKeyboardButton("📚 My Ad History", callback_data="action:history")],
    ])
    await message.reply_text(
        "✅ *Done!* Use the buttons below to share or edit your ad.",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )

    # 5. Save to history
    session.save_to_history({
        "product": session.product_name,
        "headline": copy.get("headline", ""),
        "body": copy.get("body", ""),
        "cta": copy.get("cta", ""),
        "hashtags": copy.get("hashtags", []),
        "image_url": img_url or "",
        "platform": session.platform,
    })

    session.state = State.DONE


async def deliver_copy_only(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """Fallback when image generation fails — still delivers full copy pack."""
    session = sessions.get(user_id)
    copy = session.current_copy

    ig_caption = get_instagram_caption(copy)
    wa_message = get_whatsapp_message(copy)
    wa_link    = get_whatsapp_share_link(wa_message)
    canva_link = get_canva_link(session.business_type, session.platform)

    text = (
        "📦 *Your Ad Copy Pack:*\n\n"
        "📸 *Instagram:*\n" + ig_caption + "\n\n"
        "💬 *WhatsApp:*\n" + wa_message
    )

    await _send_long_message(message, text, parse_mode="Markdown")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Share on WhatsApp", url=wa_link)],
        [InlineKeyboardButton("🎨 Create Image on Canva", url=canva_link)],
        [InlineKeyboardButton("🔁 Create Another Ad", callback_data="action:new_ad")],
    ])
    await message.reply_text(
        "🎨 No image this time — but use Canva to design one with the copy above!",
        reply_markup=keyboard,
    )
    session.state = State.DONE


async def handle_action(update, context: ContextTypes.DEFAULT_TYPE):
    """Handles post-delivery action buttons."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    action = query.data.split(":", 1)[1]

    if action == "new_ad":
        session = sessions.get(user_id)
        session.reset_for_new_ad()
        # Re-trigger start
        from bot.handlers.start import cmd_start
        await query.edit_message_text("Starting a new ad...")
        # Simulate /start
        class _FakeMsg:
            chat_id = query.message.chat_id
            async def reply_text(self, *a, **kw):
                await context.bot.send_message(chat_id=query.message.chat_id, *a[1:] if a else [], **kw)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="👇 Choose your business type:",
            reply_markup=_build_business_keyboard(),
        )
        session.state = State.CHOOSE_BUSINESS

    elif action == "history":
        from bot.handlers.history import show_history
        await show_history(query.message, context, user_id)


def _build_business_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from config import BUSINESS_TYPES
    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"btype:{key}")]
        for label, key in BUSINESS_TYPES.items()
    ]
    return InlineKeyboardMarkup(keyboard)


async def _send_long_message(message: Message, text: str, **kwargs):
    """Split messages >4000 chars to respect Telegram limits."""
    LIMIT = 4000
    if len(text) <= LIMIT:
        await message.reply_text(text, **kwargs)
        return
    parts = [text[i:i+LIMIT] for i in range(0, len(text), LIMIT)]
    for part in parts:
        await message.reply_text(part, **kwargs)
