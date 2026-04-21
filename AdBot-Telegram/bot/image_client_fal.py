"""
bot/image_client_fal.py — fal.ai FLUX image-to-image client.

⚠️  THIS FILE IS NOT ACTIVE — it is a REFERENCE IMPLEMENTATION.
⚠️  To activate it, see docs/FAL_AI_UPGRADE.md for the exact steps.

WHY FAL.AI IS BETTER THAN POLLINATIONS (for product ads):
─────────────────────────────────────────────────────────
Pollinations (text-to-image):
    You describe the product in words → AI imagines a product → random result
    Best case: looks similar to your product
    Worst case: completely different product, wrong colors, hallucinated details

fal.ai FLUX (image-to-image):
    You provide your actual product photo → AI keeps the product, changes scene
    Result: YOUR product, in a professional ad setting, every time
    This is how real ad agencies work (extract → composite → render)

QUALITY COMPARISON:
    Pollinations FLUX (text)  ★★★☆☆  Good   — much better than before, free
    fal.ai FLUX Dev (img2img) ★★★★★  Studio — agency-grade, $25 free credit

HOW IMAGE-TO-IMAGE WORKS:
    1. Take user's product photo (already stored in session.photos[0])
    2. Send it to fal.ai FLUX as the "init_image" (reference image)
    3. Send the positive prompt as guidance text
    4. strength=0.65 → AI keeps 35% of original photo structure (product shape)
       and transforms 65% (background, lighting, scene)
    5. The product maintains its actual appearance while being placed in a
       professional advertising scene

COST:
    $25 free credit on signup = ~500 ad images (at ~$0.05/image)
    After that: pay-as-you-go, still cheaper than any design tool

SETUP INSTRUCTIONS:
    1. Sign up at https://fal.ai → get API key
    2. pip install fal-client
    3. Add to .env:  FAL_API_KEY=fal-xxxxxxxxxxxxxxxx
    4. In image.py: change import from image_client to image_client_fal
    5. The function signature is identical — zero other code changes needed
"""

import os
import base64
import random
from typing import Optional, Tuple, Union

# pip install fal-client
# Add to requirements.txt: fal-client==0.5.0
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False

from bot.image_client import _huggingface, _unpack_prompt  # reuse HF fallback
PromptInput = Union[dict, str]

FAL_API_KEY = os.getenv("FAL_API_KEY", "")

# The best fal.ai model for product advertising images
# FLUX.1-dev: highest quality, best prompt following, image-to-image support
FAL_MODEL = "fal-ai/flux/dev"


def generate_image(prompt: PromptInput, product_photo: Optional[bytes] = None) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Generate an ad image using fal.ai FLUX (image-to-image when photo provided).

    Args:
        prompt:        dict {"positive": ..., "negative": ...} or plain str
        product_photo: Raw bytes of user's product photo (session.photos[0])
                       If provided → image-to-image (keeps product appearance)
                       If None     → text-to-image (same as Pollinations)

    Returns:
        (url, None)    — if fal.ai returns a URL (common)
        (None, bytes)  — if image bytes returned
        (None, None)   — failed, caller shows Canva link
    """
    if not FAL_AVAILABLE:
        raise ImportError(
            "fal-client not installed. Run: pip install fal-client\n"
            "See docs/FAL_AI_UPGRADE.md for full setup."
        )
    if not FAL_API_KEY:
        raise ValueError(
            "FAL_API_KEY not set in .env\n"
            "Get your key at: https://fal.ai/dashboard/keys"
        )

    positive, negative = _unpack_prompt(prompt)

    try:
        # ── Build fal.ai request payload ──────────────────────────────────────
        payload = {
            "prompt":          positive,
            "negative_prompt": negative,
            "num_inference_steps": 28,      # Higher = better quality (FLUX dev optimal: 25-35)
            "guidance_scale":   3.5,        # FLUX dev optimal range: 3.0-4.5
            "image_size":      "square_hd", # 1024x1024 — best for Instagram ads
            "seed":             random.randint(1, 999999),
            "enable_safety_checker": False, # Product ads are not NSFW
        }

        # ── Image-to-image: feed user's product photo as reference ────────────
        # This is the MAGIC step: the model sees the actual product and
        # keeps its visual identity while building the ad scene around it.
        if product_photo:
            # fal.ai accepts base64-encoded images or data URIs
            encoded = base64.b64encode(product_photo).decode("utf-8")
            payload["image_url"]  = f"data:image/jpeg;base64,{encoded}"
            payload["strength"]   = 0.65  # 0=copy photo exactly, 1=ignore photo
            # 0.65 means: keep product identity, transform background/scene

            # Switch to the FLUX model with image-conditioning support
            model = "fal-ai/flux/dev/image-to-image"
        else:
            # Pure text-to-image (same quality boost as img2img, just no photo reference)
            model = FAL_MODEL

        # ── Run the fal.ai call (synchronous mode) ────────────────────────────
        os.environ["FAL_KEY"] = FAL_API_KEY
        result = fal_client.run(model, arguments=payload)

        # ── Extract URL from result ───────────────────────────────────────────
        if result and result.get("images"):
            image_url = result["images"][0]["url"]
            return image_url, None

    except Exception as e:
        # Log but don't crash — fall through to HF fallback
        import logging
        logging.getLogger(__name__).error(f"fal.ai error: {e}")

    # ── Fallback: HuggingFace SDXL-Turbo ─────────────────────────────────────
    data = _huggingface(positive)
    return None, data


# ── HOW TO ACTIVATE THIS FILE ─────────────────────────────────────────────────
# In bot/handlers/image.py, change:
#
#   FROM:  from bot.image_client import generate_image
#   TO:    from bot.image_client_fal import generate_image
#
# Then update the executor call in run_generate_image() to pass the photo:
#
#   FROM:  url, img_bytes = await loop.run_in_executor(None, generate_image, img_prompt)
#   TO:    photo = session.photos[0] if session.photos else None
#          url, img_bytes = await loop.run_in_executor(
#              None, generate_image, img_prompt, photo
#          )
#
# That's it. Zero other changes needed. Full drop-in replacement.
#
# See docs/FAL_AI_UPGRADE.md for the complete guide.
# ─────────────────────────────────────────────────────────────────────────────
