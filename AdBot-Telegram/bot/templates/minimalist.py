"""bot/templates/minimalist.py — Minimalist Dark template (v2 AGENCY GRADE).

Best for: Tech, SaaS, electronics, premium products.

Layout:
  ┌──────────────────────────────────────────┐
  │  · · · · · · · · · · · · · · · · · · · │  ← scanlines + dot grid
  │                                          │
  │      ░░░░░░ ELECTRIC GLOW ░░░░░░        │
  │      ░░░  ╔═══════════════╗  ░░░        │
  │      ░░░  ║   PRODUCT     ║  ░░░        │  ← 52% hero zone, glow
  │      ░░░  ╚═══════════════╝  ░░░        │
  │      [ floor reflection ]                │
  │                                          │
  │   ╔══════════════════════════════════╗  │  ← frosted glass panel
  │   ║  HEADLINE (bold white)           ║  │
  │   ║  body text (subtle)              ║  │
  │   ╚══════════════════════════════════╝  │
  │                                          │
  │          ── CTA ──                       │  ← underlined minimal CTA
  └──────────────────────────────────────────┘
"""
import io
import math
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    enhance_product, add_drop_shadow, add_glow_behind,
    add_product_reflection, make_gradient, make_radial_glow,
    add_dot_pattern, add_scanlines, add_vignette, add_frosted_glass_panel,
    draw_text_with_shadow, wrap_text, measure_text,
)


DARK_GRADIENTS = {
    "tech":        [(8, 16, 38),    (18, 38, 80)],
    "saas":        [(10, 10, 24),   (22, 26, 58)],
    "electronics": [(6, 10, 20),    (16, 26, 52)],
    "other":       [(12, 12, 30),   (28, 28, 65)],
}

GLOW_COLORS = {
    "tech":        (0, 150, 255),
    "saas":        (110, 80, 255),
    "electronics": (0, 210, 210),
    "other":       (80, 130, 255),
}

ACCENT_COLORS = {
    "tech":        (0, 200, 255),
    "saas":        (140, 100, 255),
    "electronics": (0, 230, 220),
    "other":       (100, 160, 255),
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Minimalist dark ad — agency-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    grad_top, grad_bot = DARK_GRADIENTS.get(biz, DARK_GRADIENTS["other"])
    glow_col = brand_color or GLOW_COLORS.get(biz, GLOW_COLORS["other"])
    accent   = ACCENT_COLORS.get(biz, (100, 160, 255))

    # ── 1. Dark gradient canvas ────────────────────────────────────────────────
    canvas = make_gradient((W, H), grad_top, grad_bot).convert("RGBA")

    # ── 2. Scanlines (tech feel) ───────────────────────────────────────────────
    canvas = add_scanlines(canvas, gap=4, opacity=12)

    # ── 3. Dot grid ───────────────────────────────────────────────────────────
    canvas = add_dot_pattern(canvas, spacing=36, dot_size=2, opacity=16)

    # ── 4. Radial glow ────────────────────────────────────────────────────────
    glow_overlay = make_radial_glow(
        (W, H), (cx, int(H * 0.32)),
        glow_col, int(min(W, H) * 0.40), opacity=40
    )
    canvas = Image.alpha_composite(canvas, glow_overlay)

    # ── 5. Subtle vignette ────────────────────────────────────────────────────
    canvas = add_vignette(canvas, strength=70)

    draw = ImageDraw.Draw(canvas)

    # ── Top accent bar ─────────────────────────────────────────────────────────
    bar_h = max(4, H // 220)
    bar_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bar_layer)
    b_draw.rectangle([0, 0, W, bar_h], fill=(*glow_col[:3], 200))
    canvas = Image.alpha_composite(canvas, bar_layer)
    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT — Top half, electric glow + shadow + reflection
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.55)

    prod_zone_h = int(H * 0.52)
    prod_zone_w = int(W * 0.74)
    product.thumbnail((prod_zone_w, prod_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = int(H * 0.07)

    # Multi-layer electric glow
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=glow_col, glow_opacity=65,
        glow_radius=90, glow_scale=1.4
    )
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=tuple(min(255, c + 60) for c in glow_col),
        glow_opacity=40, glow_radius=40, glow_scale=1.15
    )
    canvas = add_drop_shadow(
        canvas, product, (px, py),
        shadow_opacity=110, shadow_offset=(0, 18), blur_radius=38
    )
    canvas = add_product_reflection(canvas, product, (px, py), opacity=35, height_fraction=0.22)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.032)

    # ══════════════════════════════════════════════════════════════════════════
    # FROSTED GLASS TEXT PANEL — headline + body
    # ══════════════════════════════════════════════════════════════════════════
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(54, W // 15)
    h_font = get_font(language, size=h_size, bold=True)
    wrapped_h = wrap_text(draw, headline, h_font, int(W * 0.82))
    h_bbox = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox[2] - h_bbox[0]
    hh = h_bbox[3] - h_bbox[1]

    body = prepare_text(safe_get(copy, "body", "")[:120], language)
    b_size = max(26, W // 34)
    b_font = get_font(language, size=b_size)
    wrapped_b = wrap_text(draw, body, b_font, int(W * 0.74))
    b_bbox = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
    bh = b_bbox[3] - b_bbox[1]

    panel_pad = int(H * 0.035)
    panel_h = hh + bh + panel_pad * 3
    panel_x1 = int(W * 0.06)
    panel_x2 = W - int(W * 0.06)
    panel_y1 = y_cursor
    panel_y2 = y_cursor + panel_h

    if panel_y2 < H - int(H * 0.12):
        canvas = add_frosted_glass_panel(
            canvas,
            (panel_x1, panel_y1, panel_x2, panel_y2),
            color=glow_col, opacity=18, radius=22, border_opacity=55
        )
        draw = ImageDraw.Draw(canvas)

        h_x = cx - hw // 2
        canvas = draw_text_with_shadow(
            canvas, (h_x, panel_y1 + panel_pad), wrapped_h, h_font,
            fill=(255, 255, 255), shadow_color=(0, 0, 0),
            shadow_offset=3, shadow_blur=10, multiline=True
        )
        draw = ImageDraw.Draw(canvas)

        # Body text
        bw = b_bbox[2] - b_bbox[0]
        bx = cx - bw // 2
        draw.multiline_text(
            (bx, panel_y1 + panel_pad + hh + int(panel_pad * 0.8)),
            wrapped_b, font=b_font,
            fill=(165, 185, 210), align="center"
        )
        y_cursor = panel_y2 + int(H * 0.030)
    else:
        # Compact: just print headline without panel
        h_x = cx - hw // 2
        canvas = draw_text_with_shadow(
            canvas, (h_x, y_cursor), wrapped_h, h_font,
            fill=(255, 255, 255), shadow_color=(0, 0, 0),
            shadow_offset=3, shadow_blur=10, multiline=True
        )
        draw = ImageDraw.Draw(canvas)
        y_cursor += hh + int(H * 0.02)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA — minimal with glowing underline
    # ══════════════════════════════════════════════════════════════════════════
    cta = prepare_text(safe_get(copy, "cta", "Learn More →"), language)
    cta_size = max(34, W // 26)
    cta_font = get_font(language, size=cta_size, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h2 = cta_bbox[3] - cta_bbox[1]

    cta_x = cx - cta_w // 2
    cta_y = min(y_cursor, H - cta_h2 - int(H * 0.055))

    # Glow underline (3 layers: wide soft, medium, thin sharp)
    underline_y = cta_y + cta_h2 + 6
    glow_layers = [(5, 60), (3, 130), (1, 220)]
    for thickness, alpha_val in glow_layers:
        ug = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ug).rectangle(
            [cta_x, underline_y, cta_x + cta_w, underline_y + thickness],
            fill=(*accent[:3], alpha_val)
        )
        ug = ug.filter(ImageFilter.GaussianBlur(radius=max(1, thickness)))
        canvas = Image.alpha_composite(canvas, ug)

    draw = ImageDraw.Draw(canvas)
    solid_line = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(solid_line).rectangle(
        [cta_x, underline_y, cta_x + cta_w, underline_y + 2],
        fill=(*accent[:3], 220)
    )
    canvas = Image.alpha_composite(canvas, solid_line)
    draw = ImageDraw.Draw(canvas)
    draw.text((cta_x, cta_y), cta, font=cta_font, fill=accent[:3])

    # ── Final output ───────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()
