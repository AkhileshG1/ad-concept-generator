"""bot/handlers/image.py — Image generation pipeline."""
import io
from telegram import Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.prompts import build_image_prompt
from bot.image_client import generate_image
from bot.quality import is_image_ok
from config import State, FREE_IMAGES_PER_DAY


async def run_generate_image(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = sessions.get(user_id)

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

    img_prompt = build_image_prompt(session)

    import asyncio
    try:
        loop = asyncio.get_running_loop()
        url, img_bytes = await loop.run_in_executor(
            None, generate_image, img_prompt
        )
    except Exception:
        url, img_bytes = None, None

    session.record_image()
    session.current_image_url = url or ""
    session.state = State.DONE

    from bot.handlers.deliver import deliver_full_pack
    await deliver_full_pack(message, context, user_id, img_url=url, img_bytes=img_bytes)
