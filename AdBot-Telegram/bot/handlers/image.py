"""bot/handlers/image.py — Image generation pipeline (v2).

Routing logic:
  - User uploaded product photo(s)  → v2 compositor pipeline
      rembg removes background → Pillow templates render pro ad
  - No photo uploaded               → v1 Pollinations FLUX fallback
      Visual DNA prompt → FLUX text-to-image

This means Pollinations is never deleted — it's always the safety net.
"""
import io
import asyncio
import logging
from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.prompts import build_image_prompt
from bot.image_client import generate_image
from config import State, FREE_IMAGES_PER_DAY

logger = logging.getLogger(__name__)


async def run_generate_image(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = sessions.get(user_id)

    # ── Rate limit check ──────────────────────────────────────────────────────
    if not session.can_generate_image():
        limit = FREE_IMAGES_PER_DAY if not session.is_pro else 10
        await message.reply_text(
            f"⚠️ Image limit reached ({limit}/day on your plan).\n\n"
            "Your ad copy is above — use Canva to create the image.\n"
            "⭐ Upgrade to PRO for more images: /upgrade",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Upgrade for more images", callback_data="buy:monthly")]
            ])
        )
        from bot.handlers.deliver import deliver_copy_only
        await deliver_copy_only(message, context, user_id)
        return

    # ── Route: compositor (v2) vs Pollinations FLUX (v1 fallback) ────────────
    if session.photos:
        await _compositor_pipeline(message, context, user_id, session)
    else:
        await _pollinations_pipeline(message, context, user_id, session)


# ─────────────────────────────────────────────────────────────────────────────
# v2 — Real Product Compositor Pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def _compositor_pipeline(message, context, user_id: int, session):
    """
    v2 pipeline: User's real product photo → bg removal → Pillow compositor.
    Stages:
      1. Background removal (rembg, ~2s)
      2. Template composition (Pillow, ~0.5s)
      3. Deliver final ad
    """
    await message.reply_text("🔍 Removing background from your product photo... (~2s)")

    copy = session.current_copy or {}
    photo_bytes = session.photos[0]  # Use first photo
    business_type = session.business_type or "other"
    platform = session.platform or "instagram"

    # Detect user language from Telegram user info
    language = "en"
    try:
        from bot.language import get_session_language
        language = get_session_language(session)
    except Exception:
        pass

    loop = asyncio.get_running_loop()

    try:
        # Run compositor in thread pool (CPU-bound)
        from bot.compositor import compose_ad

        await message.reply_text("🎨 Composing your professional ad poster...")

        img_bytes = await loop.run_in_executor(
            None,
            lambda: compose_ad(
                product_bytes=photo_bytes,
                copy=copy,
                template=None,          # auto-selected from business type
                platform=platform,
                business_type=business_type,
                language=language,
            )
        )

        if img_bytes:
            session.record_image()
            session.current_image_url = ""
            session.state = State.DONE
            logger.info(f"Compositor pipeline success for user {user_id}, {len(img_bytes):,} bytes")
            from bot.handlers.deliver import deliver_full_pack
            await deliver_full_pack(message, context, user_id, img_url=None, img_bytes=img_bytes)
            return

    except Exception as e:
        logger.error(f"Compositor pipeline failed for user {user_id}: {e}")
        await message.reply_text(
            "⚠️ Advanced compositor had an issue. Generating with AI instead..."
        )

    # Fallback: FLUX if compositor fails
    await _pollinations_pipeline(message, context, user_id, session)


# ─────────────────────────────────────────────────────────────────────────────
# v1 — Pollinations FLUX → Scene Overlay Compositor Pipeline
# ─────────────────────────────────────────────────────────────────────────────

async def _pollinations_pipeline(message, context, user_id: int, session):
    """
    v1 path: AI scene image → scene_overlay compositor → branded ad poster.

    Pipeline:
      1. Pollinations FLUX generates a photorealistic scene/product image
      2. scene_overlay template composites professional typography on top:
           - Smart crop to platform canvas size
           - Dark gradient overlay for text readability
           - Frosted glass headline panel
           - Full body text (properly wrapped, no truncation)
           - Premium CTA pill button
           - Hashtag strip
      3. Deliver the branded JPEG — never a raw AI image

    This guarantees every output looks professional regardless of image source.
    """
    copy = session.current_copy or {}
    business_type = session.business_type or "other"
    platform = session.platform or "instagram"

    language = "en"
    try:
        from bot.language import get_session_language
        language = get_session_language(session)
    except Exception:
        pass

    img_prompt = build_image_prompt(session)
    loop = asyncio.get_running_loop()

    await message.reply_text(
        "🎨 Generating your scene image… (~5-10s)"
    )

    try:
        url, img_bytes = await loop.run_in_executor(
            None, generate_image, img_prompt
        )
    except Exception as e:
        logger.error(f"Pollinations generation failed: {e}")
        url, img_bytes = None, None

    # ── Compositor pass: always overlay branding on the AI image ─────────────
    if img_bytes:
        try:
            from bot.templates import scene_overlay
            await message.reply_text("✨ Applying professional layout…")

            final_bytes = await loop.run_in_executor(
                None,
                lambda: scene_overlay.compose(
                    scene_image_bytes=img_bytes,
                    copy=copy,
                    platform=platform,
                    business_type=business_type,
                    language=language,
                )
            )
            logger.info(
                f"Scene overlay success for user {user_id}, "
                f"{len(final_bytes):,} bytes."
            )
            img_bytes = final_bytes
            url = None  # always deliver bytes, not URL
        except Exception as e:
            logger.error(
                f"Scene overlay compositor failed for user {user_id}: {e}. "
                f"Falling back to raw Pollinations image."
            )
            # img_bytes stays as raw Pollinations image — acceptable fallback

    session.record_image()
    session.current_image_url = url or ""
    session.state = State.DONE

    from bot.handlers.deliver import deliver_full_pack
    await deliver_full_pack(
        message, context, user_id,
        img_url=url if not img_bytes else None,
        img_bytes=img_bytes,
    )
