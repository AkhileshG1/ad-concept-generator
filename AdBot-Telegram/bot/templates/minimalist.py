"""bot/templates/minimalist.py — Minimalist dark template (v2 PRO).

Best for: Tech, SaaS, electronics, premium products.
Layout: Dark bg with subtle grid, product centered with blue glow, clean text.

Canvas:
┌──────────────────────────────┐
│  · · · · · · · · · · · · ·  │  ← subtle dot grid
│                              │
│     ░░░ BLUE GLOW  ░░░      │
│     ░░ [ PRODUCT ] ░░       │  ← product with electric glow
│     ░░░░░░░░░░░░░░░░░       │
│                              │
│        HEADLINE              │  ← clean white text
│        body text             │
│                              │
│        Learn More →          │  ← text CTA (no button - minimal)
└──────────────────────────────┘
"""
import io
import math
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    enhance_product, add_drop_shadow, add_glow_behind,
    make_gradient, wrap_text, measure_text,
)


DARK_GRADIENTS = {
    "tech":      [(10, 18, 35),    (20, 40, 75)],
    "saas":      [(12, 12, 25),    (25, 30, 60)],
    "electronics":[(8, 12, 20),    (18, 28, 50)],
    "other":     [(15, 15, 30),    (30, 30, 60)],
}

GLOW_COLORS = {
    "tech":      (0, 140, 255),    # electric blue
    "saas":      (100, 80, 255),   # purple
    "electronics":(0, 200, 200),   # teal
    "other":     (80, 120, 255),   # blue
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Minimalist dark ad poster — market-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    grad_top, grad_bot = DARK_GRADIENTS.get(biz, DARK_GRADIENTS["other"])
    glow_color = brand_color or GLOW_COLORS.get(biz, GLOW_COLORS["other"])

    # ── Dark gradient canvas ──────────────────────────────────────────────────
    canvas = make_gradient((W, H), grad_top, grad_bot).convert("RGBA")

    # ── Subtle dot grid (tech aesthetic) ──────────────────────────────────────
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid)
    spacing = 35
    for y in range(0, H, spacing):
        for x in range(0, W, spacing):
            g_draw.ellipse([x, y, x + 2, y + 2], fill=(255, 255, 255, 18))
    canvas = Image.alpha_composite(canvas, grid)

    # ── Subtle radial glow in center ──────────────────────────────────────────
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gl_draw = ImageDraw.Draw(glow_layer)
    glow_r = int(min(W, H) * 0.38)
    gl_draw.ellipse([cx - glow_r, int(H * 0.25) - glow_r,
                      cx + glow_r, int(H * 0.25) + glow_r],
                     fill=glow_color + (25,))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=80))
    canvas = Image.alpha_composite(canvas, glow_layer)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT — Centered in upper half with electric glow
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.5)

    prod_zone_h = int(H * 0.50)
    prod_zone_w = int(W * 0.70)
    product.thumbnail((prod_zone_w, prod_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = int(H * 0.08)

    # Electric glow behind product
    canvas = add_glow_behind(canvas, product, (px, py),
                             glow_color=glow_color, glow_opacity=60,
                             glow_radius=70, glow_scale=1.3)

    # Shadow
    canvas = add_drop_shadow(canvas, product, (px, py),
                             shadow_opacity=90, shadow_offset=(0, 15), blur_radius=30)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.04)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADLINE
    # ══════════════════════════════════════════════════════════════════════════
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(52, W // 16)
    h_font = get_font(language, size=h_size, bold=True)
    wrapped_h = wrap_text(draw, headline, h_font, int(W * 0.85))
    h_bbox_full = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox_full[2] - h_bbox_full[0]
    total_hh = h_bbox_full[3] - h_bbox_full[1]

    h_x = cx - hw // 2
    draw.multiline_text((h_x, y_cursor), wrapped_h, font=h_font, fill=(255, 255, 255))
    y_cursor += total_hh + int(H * 0.02)

    # ── Body ──────────────────────────────────────────────────────────────────
    body = prepare_text(safe_get(copy, "body")[:90], language)
    b_size = max(26, W // 34)
    b_font = get_font(language, size=b_size)
    wrapped_b = wrap_text(draw, body, b_font, int(W * 0.70))
    b_bbox_full = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
    bw = b_bbox_full[2] - b_bbox_full[0]
    total_bh = b_bbox_full[3] - b_bbox_full[1]

    b_x = cx - bw // 2
    draw.multiline_text((b_x, y_cursor), wrapped_b, font=b_font, fill=(170, 180, 200))
    y_cursor += total_bh + int(H * 0.035)

    # ── CTA — text with underline (minimal style) ────────────────────────────
    cta = prepare_text(safe_get(copy, "cta", "Learn More →"), language)
    cta_size = max(32, W // 28)
    cta_font = get_font(language, size=cta_size, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]

    cta_x = cx - cta_w // 2
    cta_y = min(y_cursor, H - cta_h - int(H * 0.06))
    draw.text((cta_x, cta_y), cta, font=cta_font, fill=glow_color)

    # Underline accent
    draw.rectangle([cta_x, cta_y + cta_h + 6, cta_x + cta_w, cta_y + cta_h + 9],
                    fill=glow_color)

    # ── Final output ──────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=93)
    return buf.getvalue()
