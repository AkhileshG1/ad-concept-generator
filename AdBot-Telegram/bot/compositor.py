"""bot/compositor.py — Professional ad composition engine (v2 core).

Orchestrates the full pipeline:
  1. bg_remover   → strip product background
  2. language     → detect user language
  3. template     → select and render the correct ad layout

Public API:
  compose_ad(product_bytes, copy, template, platform, business_type, language, brand_color)
  → bytes  (JPEG of finished ad)
"""
import io
import logging
from PIL import Image

from bot.bg_remover import remove_background, extract_dominant_color

logger = logging.getLogger(__name__)

# ── Template → business type auto-assignment ──────────────────────────────────
BUSINESS_TEMPLATE_MAP = {
    "food":      "hero_center",
    "beverage":  "hero_center",
    "fashion":   "split_screen",
    "retail":    "split_screen",
    "clothing":  "split_screen",
    "tech":      "minimalist",
    "technology":"minimalist",
    "saas":      "minimalist",
    "electronics":"minimalist",
    "services":  "bold_poster",
    "local":     "bold_poster",
    "restaurant":"bold_poster",
    "wellness":  "hero_center",
    "beauty":    "bold_poster",
    "fitness":   "bold_poster",
    "education": "bold_poster",
    "other":     "hero_center",
}

# ── Valid template names ──────────────────────────────────────────────────────
VALID_TEMPLATES = {"hero_center", "split_screen", "minimalist", "bold_poster"}

# ── Platform canvas sizes (W×H) ───────────────────────────────────────────────
CANVAS_SIZES = {
    "instagram": (1080, 1080),
    "poster":    (1080, 1350),
    "whatsapp":  (800,  800),
    "google":    (1200, 628),
}


def _auto_select_template(business_type: str, copy: dict) -> str:
    """
    Pick the best template for this business type.
    Also checks if Gemini suggested a template in the copy dict.
    """
    # Gemini can suggest a template
    suggested = copy.get("template_suggestion", "")
    if suggested and suggested in VALID_TEMPLATES:
        return suggested

    biz = (business_type or "other").lower()
    return BUSINESS_TEMPLATE_MAP.get(biz, "hero_center")


def _load_template_module(template_name: str):
    """Dynamically import the template module."""
    if template_name not in VALID_TEMPLATES:
        template_name = "hero_center"
    try:
        if template_name == "hero_center":
            from bot.templates import hero_center
            return hero_center
        elif template_name == "split_screen":
            from bot.templates import split_screen
            return split_screen
        elif template_name == "minimalist":
            from bot.templates import minimalist
            return minimalist
        elif template_name == "bold_poster":
            from bot.templates import bold_poster
            return bold_poster
    except ImportError as e:
        logger.error(f"Could not load template '{template_name}': {e}")
        from bot.templates import hero_center
        return hero_center


def compose_ad(
    product_bytes: bytes,
    copy: dict,
    template: str = None,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
    remove_bg: bool = True,
) -> bytes:
    """
    Full pipeline: background removal → template composition → JPEG output.

    Args:
        product_bytes : Raw JPEG/PNG bytes of product photo from Telegram
        copy          : Gemini JSON dict {headline, body, cta, visual_style, ...}
        template      : Force a specific template or None for auto-selection
        platform      : "instagram" | "poster" | "whatsapp"
        business_type : Used for palette + template selection
        language      : ISO 639-1 code for font selection
        brand_color   : Optional (R,G,B) override for accent colour
        remove_bg     : If False, skip background removal (use as-is)

    Returns:
        JPEG bytes of the professional ad image.
    """
    logger.info(f"compose_ad: platform={platform}, business={business_type}, lang={language}, template={template}")

    # ── Step 1: Auto-extract brand color if not provided ──────────────────────
    if brand_color is None:
        visual = copy.get("visual_style", {})
        gemini_colors = copy.get("brand_colors", [])
        if gemini_colors:
            try:
                brand_color = _hex_to_rgb(gemini_colors[0])
                logger.info(f"Using Gemini brand color: {gemini_colors[0]} → {brand_color}")
            except Exception:
                pass

    if brand_color is None:
        brand_color = extract_dominant_color(product_bytes)
        logger.info(f"Auto-extracted brand color: {brand_color}")

    # ── Step 2: Background removal ────────────────────────────────────────────
    if remove_bg:
        logger.info("Removing product background...")
        # Choose rembg model based on business type
        model = "u2net_human_seg" if business_type in ("fashion", "beauty", "fitness") else "u2net"
        product_png = remove_background(product_bytes, model=model)
    else:
        # Convert to RGBA PNG without bg removal
        img = Image.open(io.BytesIO(product_bytes)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        product_png = buf.getvalue()
        logger.info("Background removal skipped (remove_bg=False)")

    # ── Step 3: Select template ───────────────────────────────────────────────
    chosen_template = template or _auto_select_template(business_type, copy)
    logger.info(f"Using template: {chosen_template}")

    # ── Step 4: Render ────────────────────────────────────────────────────────
    try:
        tmpl = _load_template_module(chosen_template)
        result_bytes = tmpl.compose(
            product_png=product_png,
            copy=copy,
            platform=platform,
            business_type=business_type,
            language=language,
            brand_color=brand_color,
        )
        logger.info(f"Composition complete. Output: {len(result_bytes):,} bytes")
        return result_bytes

    except Exception as e:
        logger.error(f"Template '{chosen_template}' failed: {e}. Falling back to hero_center.")
        from bot.templates import hero_center
        return hero_center.compose(
            product_png=product_png,
            copy=copy,
            platform=platform,
            business_type=business_type,
            language=language,
            brand_color=brand_color,
        )


def compose_all_sizes(
    product_bytes: bytes,
    copy: dict,
    template: str = None,
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> dict:
    """
    Render the ad in all 3 platform sizes.
    Returns dict: {"instagram": bytes, "poster": bytes, "whatsapp": bytes}
    """
    # Only remove background once (expensive)
    model = "u2net_human_seg" if business_type in ("fashion", "beauty", "fitness") else "u2net"
    product_png = remove_background(product_bytes, model=model)
    if brand_color is None:
        brand_color = extract_dominant_color(product_bytes)

    chosen = template or _auto_select_template(business_type, copy)
    tmpl = _load_template_module(chosen)

    results = {}
    for platform in ["instagram", "poster", "whatsapp"]:
        try:
            results[platform] = tmpl.compose(
                product_png=product_png,
                copy=copy,
                platform=platform,
                business_type=business_type,
                language=language,
                brand_color=brand_color,
            )
        except Exception as e:
            logger.error(f"Failed to render {platform}: {e}")
            results[platform] = None

    return results


def _hex_to_rgb(hex_str: str) -> tuple:
    """Convert #RRGGBB or RRGGBB to (R, G, B)."""
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
