"""
bot/handlers/image.py — Image generation pipeline using Pollinations.ai + HF fallback.

After a successful image, control passes to deliver.py.
"""
from telegram import Message
from telegram.ext import ContextTypes

from bot.session import sessions
from bot.prompts import build_image_prompt
from bot.image_client import generate_image
from config import State


async def run_generate_image(message: Message, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    session = sessions.get(user_id)

    if not session.can_generate_image():
        await message.reply_text(
            "⚠️ You've used your daily image quota (5 images/day — free tier limit). "
            "Come back tomorrow!\n\nYou can still use your ad copy above with Canva 🎨"
        )
        from bot.handlers.deliver import deliver_copy_only
        await deliver_copy_only(message, context, user_id)
        return

    img_prompt = build_image_prompt(session)

    try:
        url, img_bytes = await context.application.loop.run_in_executor(
            None, generate_image, img_prompt
        )
    except Exception as e:
        await message.reply_text(
            f"⚠️ Image generation hit an error: `{e}`\n"
            "Delivering your ad copy + Canva link instead.",
            parse_mode="Markdown",
        )
        from bot.handlers.deliver import deliver_copy_only
        await deliver_copy_only(message, context, user_id)
        return

    session.record_image()
    session.current_image_url = url or ""
    session.state = State.DONE

    from bot.handlers.deliver import deliver_full_pack
    await deliver_full_pack(message, context, user_id, img_url=url, img_bytes=img_bytes)
