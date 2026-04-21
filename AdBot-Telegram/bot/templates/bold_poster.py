"""bot/templates/bold_poster.py — Bold Poster ad template (v2 PRO).

Best for: Services, restaurants, local businesses, education.
Layout: Vibrant header band, product in center, bullet benefits, full-width CTA.

Canvas:
┌──────────────────────────────┐
│ ██████  HEADLINE  ██████████ │  ← vibrant header band
│ ██████████████████████████   │
├──────────────────────────────┤
│                              │
│       [ PRODUCT ]            │  ← product centered, medium
│                              │
│  ✓ Benefit one here          │
│  ✓ Second great benefit      │  ← bullet points with checkmarks
│  ✓ Third compelling reason   │
│                              │
│ ╔══════════════════════════╗ │
│ ║    CALL TO ACTION        ║ │  ← full-width vibrant button
│ ╚══════════════════════════╝ │
└──────────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get, safe_bullets
from bot.templates._effects import (
    enhance_product, add_drop_shadow, make_gradient,
    wrap_text, measure_text,
)


VIBRANT_PALETTES = {
    "services":  {"bg": [(240, 240, 248), (225, 225, 240)], "header": (80, 70, 200),  "accent": (255, 90, 80)},
    "restaurant":{"bg": [(255, 245, 235), (255, 230, 210)], "header": (200, 60, 30),  "accent": (255, 180, 50)},
    "local":     {"bg": [(240, 248, 255), (220, 235, 255)], "header": (30, 100, 200), "accent": (255, 200, 50)},
    "education": {"bg": [(245, 240, 255), (230, 220, 250)], "header": (100, 50, 200), "accent": (255, 160, 50)},
    "beauty":    {"bg": [(255, 240, 245), (255, 225, 235)], "header": (200, 50, 100), "accent": (255, 220, 100)},
    "fitness":   {"bg": [(240, 245, 240), (220, 235, 220)], "header": (30, 140, 80),  "accent": (255, 200, 50)},
    "other":     {"bg": [(242, 242, 250), (228, 228, 242)], "header": (60, 60, 160),  "accent": (255, 120, 60)},
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Bold Poster ad — market-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    palette = VIBRANT_PALETTES.get(biz, VIBRANT_PALETTES["other"])
    bg_top, bg_bot = palette["bg"]
    header_color = brand_color or palette["header"]
    accent = palette["accent"]

    # ── Light gradient background ─────────────────────────────────────────────
    canvas = make_gradient((W, H), bg_top, bg_bot).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER BAND — Vibrant colored band with headline
    # ══════════════════════════════════════════════════════════════════════════
    header_h = int(H * 0.18)

    # Header gradient (darker → lighter)
    header_light = tuple(min(255, c + 40) for c in header_color)
    header_img = make_gradient((W, header_h), header_color, header_light)
    canvas.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(canvas)

    # Headline inside header
    headline = prepare_text(safe_get(copy, "headline", "Special Offer"), language)
    h_size = max(48, W // 16)
    h_font = get_font(language, size=h_size, bold=True)
    max_hw = int(W * 0.88)
    wrapped_h = wrap_text(draw, headline, h_font, max_hw)
    h_bbox_full = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox_full[2] - h_bbox_full[0]
    total_hh = h_bbox_full[3] - h_bbox_full[1]

    h_x = cx - hw // 2
    h_y = (header_h - total_hh) // 2

    draw.multiline_text((h_x, h_y), wrapped_h, font=h_font, fill=(255, 255, 255), align="center")

    y_cursor = header_h + int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT — Centered, medium size
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.3)

    prod_zone_h = int(H * 0.35)
    prod_zone_w = int(W * 0.60)
    product.thumbnail((prod_zone_w, prod_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = y_cursor

    canvas = add_drop_shadow(canvas, product, (px, py),
                             shadow_color=(80, 80, 120), shadow_opacity=80,
                             shadow_offset=(0, 12), blur_radius=20)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.025)

    # ── Thin divider line ─────────────────────────────────────────────────────
    margin = int(W * 0.08)
    draw.rectangle([margin, y_cursor, W - margin, y_cursor + 2], fill=header_color + (60,))
    y_cursor += int(H * 0.02)

    # ══════════════════════════════════════════════════════════════════════════
    # BULLET BENEFITS
    # ══════════════════════════════════════════════════════════════════════════
    bullets = safe_bullets(copy, max_items=3)
    text_color = (40, 40, 60)  # Dark text on light background

    if bullets:
        b_size = max(26, W // 32)
        b_font = get_font(language, size=b_size)
        check_font = get_font(language, size=b_size, bold=True)
        b_x = int(W * 0.10)

        for bullet in bullets:
            bt = prepare_text(bullet, language)
            # Checkmark in accent color
            draw.text((b_x, y_cursor), "✓", font=check_font, fill=header_color)
            draw.text((b_x + int(W * 0.04), y_cursor), bt, font=b_font, fill=text_color)
            y_cursor += int(H * 0.045)

        y_cursor += int(H * 0.015)
    else:
        body = prepare_text(safe_get(copy, "body")[:120], language)
        b_size = max(26, W // 32)
        b_font = get_font(language, size=b_size)
        wrapped_b = wrap_text(draw, body, b_font, int(W * 0.80))
        b_bbox_full = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
        bw = b_bbox_full[2] - b_bbox_full[0]
        total_bh = b_bbox_full[3] - b_bbox_full[1]
        b_x = cx - bw // 2
        draw.multiline_text((b_x, y_cursor), wrapped_b, font=b_font, fill=text_color)
        y_cursor += total_bh + int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA BUTTON — Full-width, vibrant
    # ══════════════════════════════════════════════════════════════════════════
    cta = prepare_text(safe_get(copy, "cta", "Order Now"), language)
    cta_size = max(34, W // 26)
    cta_font = get_font(language, size=cta_size, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_tw = cta_bbox[2] - cta_bbox[0]
    cta_th = cta_bbox[3] - cta_bbox[1]

    pad_x, pad_y = 50, 22
    btn_w = max(cta_tw + pad_x * 2, int(W * 0.75))
    btn_h = cta_th + pad_y * 2
    btn_x = cx - btn_w // 2
    btn_y = min(y_cursor, H - btn_h - int(H * 0.04))

    # Button shadow
    shadow_btn = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sb_draw = ImageDraw.Draw(shadow_btn)
    sb_draw.rounded_rectangle([btn_x + 3, btn_y + 5, btn_x + btn_w + 3, btn_y + btn_h + 5],
                               radius=btn_h // 2, fill=(0, 0, 0, 60))
    shadow_btn = shadow_btn.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = Image.alpha_composite(canvas, shadow_btn)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                            radius=btn_h // 2, fill=header_color)

    tx = cx - cta_tw // 2
    ty = btn_y + pad_y
    draw.text((tx, ty), cta, font=cta_font, fill=(255, 255, 255))

    # ── Final output ──────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=93)
    return buf.getvalue()
