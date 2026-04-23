"""bot/templates/hero_center.py — Hero Center ad template (v2 AGENCY GRADE).

Best for: Food, beverage, lifestyle, wellness products.
Layout:
  ┌──────────────────────────────────────────┐
  │  [BADGE]          BRAND                  │  ← top bar with badge
  │  ─────────────────────────────────────── │
  │                                          │
  │   ░░░░░░░ MULTI-LAYER GLOW ░░░░░░░      │
  │   ░░░  ╔══════════════╗  ░░░            │
  │   ░░░  ║   PRODUCT    ║  ░░░            │  ← 58%+ hero zone
  │   ░░░  ╚══════════════╝  ░░░            │
  │   ░░  floor reflection  ░░░             │
  │                                          │
  │  ╔══════════════════════════════════╗   │
  │  ║   frosted glass text panel       ║   │  ← glassmorphism text zone
  │  ║   HEADLINE (bold, shadow)        ║   │
  │  ║   body copy (wrapped)            ║   │
  │  ╚══════════════════════════════════╝   │
  │                                          │
  │   ╔══════════════════════════════╗      │
  │   ║      CALL TO ACTION          ║      │  ← full-width pill button
  │   ╚══════════════════════════════╝      │
  └──────────────────────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    enhance_product, add_drop_shadow, add_glow_behind,
    add_product_reflection, make_gradient, make_radial_glow,
    add_dot_pattern, add_vignette, add_frosted_glass_panel,
    draw_text_with_shadow, wrap_text, measure_text,
)


# ── Agency-grade vibrant gradient palettes ─────────────────────────────────────
GRADIENTS = {
    "food":      [(255, 95, 50),   (200, 30, 100)],   # bold coral → crimson
    "fashion":   [(18, 12, 45),    (60, 20, 100)],     # deep navy → rich violet
    "tech":      [(8, 20, 50),     (20, 60, 140)],     # midnight → electric blue
    "services":  [(75, 50, 200),   (150, 60, 220)],    # indigo → violet
    "wellness":  [(20, 100, 70),   (80, 190, 130)],    # forest → mint
    "beauty":    [(160, 30, 100),  (240, 120, 170)],   # magenta → rose
    "beverage":  [(200, 80, 20),   (255, 190, 80)],    # burnt orange → amber
    "other":     [(40, 30, 100),   (100, 50, 180)],    # deep indigo → purple
}

ACCENT_COLORS = {
    "food":      (255, 230, 70),   # golden yellow
    "fashion":   (255, 120, 150),  # coral pink
    "tech":      (0, 210, 255),    # cyan
    "services":  (255, 225, 90),   # gold
    "wellness":  (170, 255, 200),  # mint
    "beauty":    (255, 240, 180),  # cream
    "beverage":  (255, 230, 90),   # amber
    "other":     (255, 215, 70),   # gold
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Hero Center ad — agency-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 215, 70))

    # ── 1. Canvas: rich gradient ───────────────────────────────────────────────
    canvas = make_gradient((W, H), grad_top, grad_bot).convert("RGBA")

    # ── 2. Dot pattern texture ─────────────────────────────────────────────────
    canvas = add_dot_pattern(canvas, spacing=42, dot_size=2, opacity=10)

    # ── 3. Central radial glow (warm spotlight) ────────────────────────────────
    bright_centre = tuple(min(255, c + 80) for c in grad_top)
    glow = make_radial_glow(
        (W, H), (cx, int(H * 0.42)),
        bright_centre, int(min(W, H) * 0.47), opacity=60
    )
    canvas = Image.alpha_composite(canvas, glow)

    # ── 4. Vignette for depth ──────────────────────────────────────────────────
    canvas = add_vignette(canvas, strength=55)

    draw = ImageDraw.Draw(canvas)
    rtl = is_rtl(language)

    # ══════════════════════════════════════════════════════════════════════════
    # TOP BAR — thin accent line + hashtag strip
    # ══════════════════════════════════════════════════════════════════════════
    bar_h = max(5, H // 200)
    draw.rectangle([0, 0, W, bar_h], fill=accent)

    # Business type label (small caps top-right)
    cat_size = max(18, W // 52)
    cat_font = get_font(language, size=cat_size, bold=True)
    cat_text = (biz or "AD").upper()
    cw, ch = measure_text(draw, cat_text, cat_font)
    draw.text((W - cw - int(W * 0.04), bar_h + int(H * 0.012)),
              cat_text, font=cat_font, fill=(*accent, 200))

    y_cursor = bar_h + int(H * 0.06)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADLINE — Bold, large, text-shadow
    # ══════════════════════════════════════════════════════════════════════════
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(62, W // 13)
    h_font = get_font(language, size=h_size, bold=True)

    max_text_w = int(W * 0.84)
    wrapped_h = wrap_text(draw, headline, h_font, max_text_w)
    h_bbox = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox[2] - h_bbox[0]
    hh = h_bbox[3] - h_bbox[1]
    h_x = cx - hw // 2

    canvas = draw_text_with_shadow(
        canvas, (h_x, y_cursor), wrapped_h, h_font,
        fill=(255, 255, 255), shadow_color=(0, 0, 0),
        shadow_offset=4, shadow_blur=12, multiline=True
    )
    draw = ImageDraw.Draw(canvas)
    y_cursor += hh + int(H * 0.018)

    # Accent line under headline
    line_w = min(hw, int(W * 0.22))
    draw.rounded_rectangle(
        [cx - line_w // 2, y_cursor, cx + line_w // 2, y_cursor + 5],
        radius=3, fill=accent,
    )
    y_cursor += int(H * 0.03)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT IMAGE — Hero zone, maximised, glow + shadow + reflection
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.4)

    remaining_h = H - y_cursor - int(H * 0.28)
    product_zone_h = max(int(remaining_h * 0.92), int(H * 0.40))
    product_zone_w = int(W * 0.80)

    product.thumbnail((product_zone_w, product_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = y_cursor + max(0, (remaining_h - ph) // 6)

    # Multi-layer glow halo
    glow_col = tuple(min(255, c + 100) for c in accent)
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=glow_col, glow_opacity=55,
        glow_radius=80, glow_scale=1.4
    )
    # White inner halo
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=(255, 255, 255), glow_opacity=30,
        glow_radius=35, glow_scale=1.10
    )

    # Drop shadow
    canvas = add_drop_shadow(
        canvas, product, (px, py),
        shadow_opacity=140, shadow_offset=(0, 22), blur_radius=40
    )

    # Floor reflection
    canvas = add_product_reflection(canvas, product, (px, py), opacity=40, height_fraction=0.2)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.018)

    # ══════════════════════════════════════════════════════════════════════════
    # FROSTED GLASS TEXT PANEL — body text inside
    # ══════════════════════════════════════════════════════════════════════════
    body_raw = safe_get(copy, "body", "")
    # Allow up to 140 chars for more content
    body = prepare_text(body_raw[:140], language)
    b_size = max(28, W // 27)
    b_font = get_font(language, size=b_size)

    wrapped_body = wrap_text(draw, body, b_font, int(W * 0.76))
    b_bbox = draw.multiline_textbbox((0, 0), wrapped_body, font=b_font)
    bw = b_bbox[2] - b_bbox[0]
    bh = b_bbox[3] - b_bbox[1]

    # Panel geometry
    pad_panel = int(W * 0.04)
    panel_x1 = int(W * 0.06)
    panel_x2 = W - int(W * 0.06)
    panel_y1 = y_cursor
    panel_y2 = y_cursor + bh + pad_panel * 2

    if body and panel_y2 < H - int(H * 0.15):
        canvas = add_frosted_glass_panel(
            canvas, (panel_x1, panel_y1, panel_x2, panel_y2),
            color=(255, 255, 255), opacity=20, radius=18, border_opacity=50
        )
        draw = ImageDraw.Draw(canvas)
        b_x = cx - bw // 2
        draw.multiline_text(
            (b_x, panel_y1 + pad_panel), wrapped_body,
            font=b_font, fill=(240, 240, 245), align="center"
        )
        y_cursor = panel_y2 + int(H * 0.025)
    else:
        y_cursor += int(H * 0.02)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA BUTTON — Full-width pill, gradient fill, shadow
    # ══════════════════════════════════════════════════════════════════════════
    cta_text = prepare_text(safe_get(copy, "cta", "Get Yours Now →"), language)
    cta_size = max(36, W // 24)
    cta_font = get_font(language, size=cta_size, bold=True)

    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_tw = cta_bbox[2] - cta_bbox[0]
    cta_th = cta_bbox[3] - cta_bbox[1]

    pad_x, pad_y = 65, 26
    btn_w = max(cta_tw + pad_x * 2, int(W * 0.60))
    btn_h = cta_th + pad_y * 2
    btn_x = cx - btn_w // 2
    btn_y = min(y_cursor, H - btn_h - int(H * 0.035))

    # Button drop shadow
    shad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2 = ImageDraw.Draw(shad)
    s2.rounded_rectangle(
        [btn_x + 4, btn_y + 8, btn_x + btn_w + 4, btn_y + btn_h + 8],
        radius=btn_h // 2, fill=(0, 0, 0, 90)
    )
    shad = shad.filter(ImageFilter.GaussianBlur(radius=12))
    canvas = Image.alpha_composite(canvas, shad)
    draw = ImageDraw.Draw(canvas)

    # Button fill (gradient inside button via horizontal lines)
    btn_img = make_gradient(
        (btn_w, btn_h),
        tuple(min(255, c + 30) for c in accent),
        tuple(max(0, c - 20) for c in accent),
    )
    btn_rgba = btn_img.convert("RGBA")
    mask = Image.new("L", (btn_w, btn_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, btn_w, btn_h], radius=btn_h // 2, fill=230
    )
    btn_rgba.putalpha(mask)
    canvas.paste(btn_rgba, (btn_x, btn_y), btn_rgba)
    draw = ImageDraw.Draw(canvas)

    # Button text
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_color = (15, 15, 15) if brightness > 130 else (255, 255, 255)
    tx = cx - cta_tw // 2
    ty = btn_y + pad_y
    draw.text((tx, ty), cta_text, font=cta_font, fill=btn_text_color)

    # Hashtags strip at very bottom
    tags = copy.get("hashtags", [])
    if tags:
        tag_str = "  ".join(f"#{t}" if not t.startswith("#") else t for t in tags[:4])
        tag_size = max(16, W // 60)
        tag_font = get_font(language, size=tag_size)
        tag_y = H - int(H * 0.028)
        tw2, th2 = measure_text(draw, tag_str, tag_font)
        draw.text((cx - tw2 // 2, tag_y), tag_str, font=tag_font,
                  fill=(*accent[:3], 140))

    # ── Final output ───────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()
