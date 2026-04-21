"""bot/templates/split_screen.py — Split Screen ad template.

Best for: Fashion, retail, clothing, accessories.
Layout: Product on left half, text on right half.

Canvas (default 1080×1080):
┌────────────────────────┐
│          │             │
│ PRODUCT  │  HEADLINE   │
│   PNG    │  ─────────  │
│ (on grad)│  body text  │
│          │             │
│          │  [ CTA ]    │
│          │             │
└────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get, safe_brand_color

GRADIENTS = {
    "food":      [(255, 107, 53),  (255, 195, 113)],
    "fashion":   [(26,  26,  46),  (22,  33,  62)],
    "tech":      [(13,  17,  23),  (22,  27,  34)],
    "services":  [(102, 126, 234), (118, 75, 162)],
    "wellness":  [(86,  171, 47),  (168, 224, 99)],
    "beauty":    [(248, 187, 217), (233, 30,  140)],
    "other":     [(30,  30,  50),  (60,  60,  100)],
}

ACCENT_COLORS = {
    "food":      (255, 107, 53),
    "fashion":   (233, 69,  96),
    "tech":      (88,  166, 255),
    "services":  (118, 75,  162),
    "wellness":  (86,  171, 47),
    "beauty":    (233, 30,  140),
    "other":     (255, 215, 0),
}

TEXT_PANEL_DARK = (15, 15, 25)


def _vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _wrap_text(draw, text, font, max_width):
    if not text:
        return ""
    words = text.split()
    lines, current = [], []
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


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "fashion",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    sizes = {"instagram": (1080, 1080), "poster": (1080, 1350), "whatsapp": (800, 800)}
    W, H = sizes.get(platform, (1080, 1080))

    biz = (business_type or "fashion").lower()
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["fashion"])
    accent = brand_color or ACCENT_COLORS.get(biz, (233, 69, 96))
    rtl = is_rtl(language)

    # Split point: 50/50
    split = W // 2

    # ── Left panel — product on gradient ─────────────────────────────────────
    left_bg = _vertical_gradient((split, H), grad_top, grad_bot).convert("RGBA")

    # Load and scale product
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    max_pw = int(split * 0.85)
    max_ph = int(H * 0.80)
    product.thumbnail((max_pw, max_ph), Image.LANCZOS)
    pw, ph = product.size
    px = (split - pw) // 2
    py = (H - ph) // 2

    # Drop shadow
    shadow = Image.new("RGBA", (split, H), (0, 0, 0, 0))
    shadow_mask = Image.new("RGBA", product.size, (0, 0, 0, 70))
    if product.mode == "RGBA":
        shadow_mask.putalpha(product.getchannel("A"))
    shadow.paste(shadow_mask, (px + 10, py + 14), shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
    left_bg = Image.alpha_composite(left_bg, shadow)
    left_bg.paste(product, (px, py), product)

    # ── Right panel — dark text zone ──────────────────────────────────────────
    right_bg = Image.new("RGBA", (W - split, H), TEXT_PANEL_DARK + (255,))
    right_draw = ImageDraw.Draw(right_bg)

    # Accent bar at top of right panel
    right_draw.rectangle([0, 0, W - split, 6], fill=accent)

    text_x = 50
    text_max_w = (W - split) - 80
    cy = int(H * 0.12)

    # Brand label (small tag)
    tag_font = get_font(language, size=22, bold=True)
    tag_text = prepare_text(safe_get(copy, "headline", business_type.upper() if business_type else "AD")[:20], language)
    right_draw.text((text_x, cy), tag_text, font=tag_font, fill=accent)
    cy += 40

    # Headline
    h_font = get_font(language, size=max(44, W // 22), bold=True)
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    wrapped_h = _wrap_text(right_draw, headline, h_font, text_max_w)
    right_draw.text((text_x, cy), wrapped_h, font=h_font, fill=(255, 255, 255))
    n_hlines = wrapped_h.count("\n") + 1
    hbbox = right_draw.textbbox((0, 0), wrapped_h, font=h_font)
    cy += (hbbox[3] - hbbox[1]) * n_hlines + 20

    # Separator line
    right_draw.rectangle([text_x, cy, text_x + 60, cy + 3], fill=accent)
    cy += 24

    # Body text
    b_font = get_font(language, size=max(26, W // 36))
    body = prepare_text(safe_get(copy, "body")[:140], language)
    wrapped_b = _wrap_text(right_draw, body, b_font, text_max_w)
    right_draw.text((text_x, cy), wrapped_b, font=b_font, fill=(190, 190, 200))
    n_blines = wrapped_b.count("\n") + 1
    bbbox = right_draw.textbbox((0, 0), wrapped_b, font=b_font)
    cy += (bbbox[3] - bbbox[1]) * n_blines + 40

    # CTA button
    cta = prepare_text(safe_get(copy, "cta", "Shop Now →"), language)
    cta_font = get_font(language, size=30, bold=True)
    c_bbox = right_draw.textbbox((0, 0), cta, font=cta_font)
    cw, ch = c_bbox[2] - c_bbox[0], c_bbox[3] - c_bbox[1]
    pad_x, pad_y = 40, 16
    btn_w = cw + pad_x * 2
    right_draw.rounded_rectangle(
        [text_x, cy, text_x + btn_w, cy + ch + pad_y * 2],
        radius=(ch + pad_y * 2) // 2,
        fill=accent,
    )
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_color = (20, 20, 20) if brightness > 128 else (255, 255, 255)
    right_draw.text((text_x + pad_x, cy + pad_y), cta, font=cta_font, fill=btn_text_color)

    # ── Combine panels ────────────────────────────────────────────────────────
    canvas = Image.new("RGBA", (W, H))
    canvas.paste(left_bg, (0, 0))
    canvas.paste(right_bg, (split, 0))

    # Thin vertical separator
    sep_draw = ImageDraw.Draw(canvas)
    sep_draw.line([(split, 0), (split, H)], fill=accent + (180,), width=3)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()
