"""bot/templates/bold_poster.py — Bold Poster ad template (v2 AGENCY GRADE).

Best for: Services, restaurants, local businesses, education, beauty, fitness.

Layout:
  ┌──────────────────────────────────────────┐
  │ ████████████ HEADER BAND ██████████████ │  ← gradient band, headline
  │ █████████████████████████████████████   │
  ├──────────────────────────────────────────┤
  │                                          │
  │        ░░░ GLOW ░░░░░                   │
  │        ░░ [ PRODUCT ] ░░                │  ← hero product, centered
  │        ░░░░░░░░░░░░░░░░                 │
  │        [ floor reflection ]              │
  ├──────────────────────────────────────────┤
  │  ✓ Benefit one here                      │  ← accent checkmarks
  │  ✓ Second great benefit                  │
  │  ✓ Third compelling reason               │
  ├──────────────────────────────────────────┤
  │   ╔════════════════════════════════╗    │
  │   ║       CALL TO ACTION          ║    │  ← full-width vibrant button
  │   ╚════════════════════════════════╝    │
  └──────────────────────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get, safe_bullets
from bot.templates._effects import (
    enhance_product, add_drop_shadow, add_glow_behind,
    add_product_reflection, make_gradient, make_radial_glow,
    add_dot_pattern, add_vignette, add_frosted_glass_panel,
    draw_text_with_shadow, wrap_text, measure_text,
)


VIBRANT_PALETTES = {
    "services":  {
        "bg_top": (232, 232, 248), "bg_bot": (210, 210, 238),
        "header": (60, 50, 195), "header_bot": (110, 60, 220),
        "accent": (255, 80, 70), "text": (30, 25, 70),
    },
    "restaurant": {
        "bg_top": (255, 242, 228), "bg_bot": (255, 220, 195),
        "header": (195, 55, 25), "header_bot": (240, 100, 40),
        "accent": (255, 190, 40), "text": (70, 25, 10),
    },
    "local": {
        "bg_top": (230, 242, 255), "bg_bot": (210, 228, 255),
        "header": (20, 90, 200),  "header_bot": (60, 140, 240),
        "accent": (255, 195, 40), "text": (15, 45, 100),
    },
    "education": {
        "bg_top": (242, 235, 255), "bg_bot": (225, 210, 252),
        "header": (85, 40, 200),  "header_bot": (130, 60, 240),
        "accent": (255, 155, 40), "text": (50, 20, 100),
    },
    "beauty": {
        "bg_top": (255, 238, 245), "bg_bot": (255, 218, 232),
        "header": (195, 40, 95),  "header_bot": (240, 90, 140),
        "accent": (255, 220, 100), "text": (90, 20, 55),
    },
    "fitness": {
        "bg_top": (232, 248, 235), "bg_bot": (210, 238, 215),
        "header": (25, 135, 70),  "header_bot": (60, 185, 110),
        "accent": (255, 210, 40), "text": (15, 65, 35),
    },
    "other": {
        "bg_top": (238, 238, 252), "bg_bot": (220, 220, 242),
        "header": (50, 50, 165),  "header_bot": (90, 70, 210),
        "accent": (255, 115, 55), "text": (30, 28, 80),
    },
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Bold Poster ad — agency-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    palette = VIBRANT_PALETTES.get(biz, VIBRANT_PALETTES["other"])
    bg_top = palette["bg_top"]
    bg_bot = palette["bg_bot"]
    header_col  = tuple(brand_color or palette["header"])
    header_bot  = palette.get("header_bot", palette["header"])
    accent      = palette["accent"]
    text_color  = palette["text"]

    # ── 1. Light gradient background ──────────────────────────────────────────
    canvas = make_gradient((W, H), bg_top, bg_bot).convert("RGBA")
    canvas = add_dot_pattern(canvas, spacing=45, dot_size=2, opacity=8)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADER BAND — gradient, headline, accent border
    # ══════════════════════════════════════════════════════════════════════════
    header_h = int(H * 0.19)

    header_img = make_gradient((W, header_h), header_col, header_bot)
    header_rgba = header_img.convert("RGBA")
    # Subtle dot texture on header
    header_rgba = add_dot_pattern(header_rgba, spacing=30, dot_size=2, opacity=15)
    canvas.paste(header_rgba.convert("RGB"), (0, 0))
    canvas = canvas.convert("RGBA")

    # Bold bottom border on header
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, header_h - 5, W, header_h], fill=accent)

    # Headline inside header
    headline = prepare_text(safe_get(copy, "headline", "Special Offer"), language)
    h_size = max(50, W // 15)
    h_font = get_font(language, size=h_size, bold=True)
    max_hw = int(W * 0.86)
    wrapped_h = wrap_text(draw, headline, h_font, max_hw)
    h_bbox = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox[2] - h_bbox[0]
    hh = h_bbox[3] - h_bbox[1]
    h_x = cx - hw // 2
    h_y = (header_h - hh) // 2 - 4

    canvas = draw_text_with_shadow(
        canvas, (h_x, h_y), wrapped_h, h_font,
        fill=(255, 255, 255), shadow_color=(0, 0, 0),
        shadow_offset=3, shadow_blur=10, multiline=True
    )
    draw = ImageDraw.Draw(canvas)

    y_cursor = header_h + int(H * 0.022)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT — Centered, large, glow + shadow + reflection
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.35)

    # Leave room for bullets + button
    bullet_count = min(len(safe_bullets(copy, max_items=3)), 3)
    space_for_bullets = int(H * 0.055) * bullet_count + int(H * 0.04)
    space_for_button  = int(H * 0.10)
    available_h = H - y_cursor - space_for_bullets - space_for_button - int(H * 0.05)

    prod_zone_h = max(int(available_h * 0.90), int(H * 0.30))
    prod_zone_w = int(W * 0.65)
    product.thumbnail((prod_zone_w, prod_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = y_cursor

    # Glow in accent colour
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=tuple(min(255, c + 60) for c in accent),
        glow_opacity=50, glow_radius=60, glow_scale=1.3
    )
    canvas = add_drop_shadow(
        canvas, product, (px, py),
        shadow_color=(50, 50, 100), shadow_opacity=110,
        shadow_offset=(0, 14), blur_radius=25
    )
    canvas = add_product_reflection(canvas, product, (px, py), opacity=30, height_fraction=0.18)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.02)

    # ── Divider line ──────────────────────────────────────────────────────────
    margin = int(W * 0.07)
    draw.rectangle([margin, y_cursor, W - margin, y_cursor + 3], fill=(*header_col[:3], 80))
    y_cursor += int(H * 0.022)

    # ══════════════════════════════════════════════════════════════════════════
    # BULLET BENEFITS
    # ══════════════════════════════════════════════════════════════════════════
    bullets = safe_bullets(copy, max_items=3)
    b_size = max(27, W // 31)
    b_font = get_font(language, size=b_size)
    check_font = get_font(language, size=b_size + 4, bold=True)
    b_x = int(W * 0.09)
    check_x = b_x
    text_x  = b_x + int(W * 0.045)

    if bullets:
        for bullet in bullets:
            bt = prepare_text(bullet, language)
            draw.text((check_x, y_cursor), "✓", font=check_font, fill=header_col)
            draw.text((text_x, y_cursor + 3), bt, font=b_font, fill=text_color)
            y_cursor += int(H * 0.053)
        y_cursor += int(H * 0.012)
    else:
        # Fall back to body text inside a frosted panel
        body = prepare_text(safe_get(copy, "body", "")[:130], language)
        wrapped_b = wrap_text(draw, body, b_font, int(W * 0.80))
        b_bbox = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
        bw = b_bbox[2] - b_bbox[0]
        bh = b_bbox[3] - b_bbox[1]
        b_x2 = cx - bw // 2
        draw.multiline_text((b_x2, y_cursor), wrapped_b, font=b_font, fill=text_color, align="center")
        y_cursor += bh + int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA BUTTON — Full-width, gradient fill, pill shape
    # ══════════════════════════════════════════════════════════════════════════
    cta = prepare_text(safe_get(copy, "cta", "Order Now"), language)
    cta_size = max(36, W // 25)
    cta_font = get_font(language, size=cta_size, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_tw = cta_bbox[2] - cta_bbox[0]
    cta_th = cta_bbox[3] - cta_bbox[1]

    pad_x, pad_y = 55, 24
    btn_w = max(cta_tw + pad_x * 2, int(W * 0.76))
    btn_h = cta_th + pad_y * 2
    btn_x = cx - btn_w // 2
    btn_y = min(y_cursor, H - btn_h - int(H * 0.035))

    # Button shadow
    shad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2 = ImageDraw.Draw(shad)
    s2.rounded_rectangle(
        [btn_x + 4, btn_y + 8, btn_x + btn_w + 4, btn_y + btn_h + 8],
        radius=btn_h // 2, fill=(0, 0, 0, 70)
    )
    shad = shad.filter(ImageFilter.GaussianBlur(radius=10))
    canvas = Image.alpha_composite(canvas, shad)
    draw = ImageDraw.Draw(canvas)

    # Gradient button
    btn_img = make_gradient(
        (btn_w, btn_h),
        tuple(min(255, c + 25) for c in header_col[:3]),
        tuple(max(0, c - 20)  for c in header_col[:3]),
    )
    btn_rgba = btn_img.convert("RGBA")
    mask = Image.new("L", (btn_w, btn_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, btn_w, btn_h], radius=btn_h // 2, fill=230)
    btn_rgba.putalpha(mask)
    canvas.paste(btn_rgba, (btn_x, btn_y), btn_rgba)
    draw = ImageDraw.Draw(canvas)

    draw.text((cx - cta_tw // 2, btn_y + pad_y), cta, font=cta_font, fill=(255, 255, 255))

    # ── Final output ───────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()
