"""bot/templates/hero_center.py — Hero Center ad template.

Best for: Food, beverage, lifestyle, wellness products.
Layout: Product centered on gradient bg, headline above, CTA below.

Canvas (default 1080×1080):
┌────────────────────────┐
│  BRAND / TAGLINE TOP   │
│                        │
│   ╔══════════════╗     │
│   ║  HEADLINE    ║     │
│   ╚══════════════╝     │
│                        │
│      [Product PNG]     │
│      (centered)        │
│                        │
│   body / tagline text  │
│                        │
│   [ CALL TO ACTION ]   │
│                        │
└────────────────────────┘
"""
import io
import math
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl


# ── Industry gradient palettes ──────────────────────────────────────────────
GRADIENTS = {
    "food":      [(255, 107, 53),  (255, 195, 113)],   # sunset orange → warm gold
    "fashion":   [(26,  26,  46),  (22,  33,  62)],    # deep navy → midnight
    "tech":      [(13,  17,  23),  (22,  27,  34)],    # github dark
    "services":  [(102, 126, 234), (118, 75, 162)],    # purple gradient
    "wellness":  [(86,  171, 47),  (168, 224, 99)],    # green gradient
    "beauty":    [(248, 187, 217), (233, 30,  140)],   # pink gradient
    "other":     [(30,  30,  50),  (60,  60,  100)],   # default dark blue
}

ACCENT_COLORS = {
    "food":      (255, 255, 255),
    "fashion":   (233, 69,  96),
    "tech":      (88,  166, 255),
    "services":  (255, 255, 255),
    "wellness":  (255, 255, 255),
    "beauty":    (26,  26,  46),
    "other":     (255, 215, 0),
}


def _make_gradient(size: tuple, top_color: tuple, bottom_color: tuple) -> Image.Image:
    """Create a vertical gradient background."""
    w, h = size
    base = Image.new("RGB", size)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return base


def _add_product_shadow(canvas: Image.Image, product: Image.Image, pos: tuple, shadow_opacity: int = 80) -> Image.Image:
    """Paste product with a soft drop shadow."""
    shadow_offset = (12, 16)
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_product = Image.new("RGBA", product.size, (0, 0, 0, shadow_opacity))
    if product.mode == "RGBA":
        shadow_product.putalpha(product.getchannel("A"))
    shadow.paste(
        shadow_product,
        (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]),
        shadow_product,
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)
    canvas.paste(product, pos, product if product.mode == "RGBA" else None)
    return canvas


def _draw_cta_button(draw: ImageDraw.Draw, text: str, center_x: int, y: int,
                     accent: tuple, language: str, w: int) -> int:
    """Draw a rounded CTA button. Returns bottom y of button."""
    font = get_font(language, 32, bold=True)
    text = prepare_text(text, language)

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    padding_x, padding_y = 50, 20
    btn_w = tw + padding_x * 2
    btn_h = th + padding_y * 2
    btn_x = center_x - btn_w // 2
    btn_y = y

    # Button background
    draw.rounded_rectangle(
        [btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
        radius=btn_h // 2,
        fill=accent,
    )

    # Button text (contrast color)
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    text_color = (20, 20, 20) if brightness > 128 else (255, 255, 255)

    tx = btn_x + padding_x
    ty = btn_y + padding_y
    if is_rtl(language):
        tx = btn_x + btn_w - padding_x - tw
    draw.text((tx, ty), text, font=font, fill=text_color)

    return btn_y + btn_h


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """
    Render a Hero Center ad poster.

    Args:
        product_png: RGBA PNG bytes (transparent bg)
        copy: Gemini JSON dict with headline, body, cta keys
        platform: "instagram" | "poster" | "whatsapp"
        business_type: Used for gradient palette selection
        language: ISO 639-1 code for font selection
        brand_color: Optional (R,G,B) override for accent color

    Returns:
        JPEG bytes of the finished ad
    """
    # Canvas sizes
    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2  # center x

    # Gradient palette
    biz = business_type.lower() if business_type else "other"
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 215, 0))

    # Build canvas
    canvas = _make_gradient((W, H), grad_top, grad_bot).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # ── Subtle radial glow in center ──────────────────────────────────────────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_r = min(W, H) // 2
    glow_color = tuple(min(255, c + 40) for c in grad_top) + (60,)
    glow_draw.ellipse([cx - glow_r, H // 2 - glow_r, cx + glow_r, H // 2 + glow_r], fill=glow_color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=120))
    canvas = Image.alpha_composite(canvas, glow)
    draw = ImageDraw.Draw(canvas)

    rtl = is_rtl(language)

    # ── Headline ──────────────────────────────────────────────────────────────
    headline = prepare_text(copy.get("headline", ""), language)
    h_font = get_font(language, size=max(48, W // 18), bold=True)
    h_color = (255, 255, 255)

    # Word-wrap headline to fit width (max 80% of canvas)
    max_text_w = int(W * 0.80)
    wrapped_headline = _wrap_text(draw, headline, h_font, max_text_w)
    h_bbox = draw.textbbox((0, 0), wrapped_headline, font=h_font)
    h_w = h_bbox[2] - h_bbox[0]
    h_h = (h_bbox[3] - h_bbox[1]) * (wrapped_headline.count("\n") + 1)

    h_x = cx - h_w // 2
    h_y = int(H * 0.06)
    draw.text((h_x, h_y), wrapped_headline, font=h_font, fill=h_color, align="center" if not rtl else "right")
    y_cursor = h_y + h_h + int(H * 0.02)

    # ── Thin accent line under headline ───────────────────────────────────────
    line_w = min(h_w, W // 3)
    draw.rectangle([cx - line_w // 2, y_cursor, cx + line_w // 2, y_cursor + 3], fill=accent)
    y_cursor += int(H * 0.03)

    # ── Product image (center, 50% of canvas height) ──────────────────────────
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product_zone_h = int(H * 0.48)
    product_zone_w = int(W * 0.80)

    # Scale product to fit zone while preserving aspect ratio
    product.thumbnail((product_zone_w, product_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = y_cursor

    canvas = _add_product_shadow(canvas, product, (px, py))
    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.03)

    # ── Body / tagline ────────────────────────────────────────────────────────
    body = prepare_text(copy.get("body", "")[:120], language)  # limit length
    b_font = get_font(language, size=max(28, W // 30))
    b_color = (220, 220, 220)
    wrapped_body = _wrap_text(draw, body, b_font, int(W * 0.75))
    b_bbox = draw.textbbox((0, 0), wrapped_body, font=b_font)
    b_w = b_bbox[2] - b_bbox[0]
    b_x = cx - b_w // 2
    draw.text((b_x, y_cursor), wrapped_body, font=b_font, fill=b_color, align="center")
    blines = wrapped_body.count("\n") + 1
    b_line_h = b_bbox[3] - b_bbox[1]
    y_cursor += b_line_h * blines + int(H * 0.025)

    # ── CTA button ────────────────────────────────────────────────────────────
    cta = copy.get("cta", "Get Yours Now →")
    _draw_cta_button(draw, cta, cx, y_cursor, accent, language, W)

    # ── Convert to JPEG ───────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _wrap_text(draw: ImageDraw.Draw, text: str, font, max_width: int) -> str:
    """Wrap text to fit within max_width pixels."""
    if not text:
        return ""
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)
