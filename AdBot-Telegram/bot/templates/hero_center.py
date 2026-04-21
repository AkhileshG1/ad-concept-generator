"""bot/templates/hero_center.py — Hero Center ad template (v2 PRO).

Best for: Food, beverage, lifestyle, wellness products.
Layout: Large product centered, bold headline above, prominent CTA below.

Design philosophy:
  - Product takes 55% of canvas height (HERO treatment)
  - Vibrant gradients (never dark/muddy)
  - Auto-brightness on dark products
  - White glow halo behind product for depth
  - Large bold typography with text shadows
  - Rounded CTA button with contrast color

Canvas (default 1080×1080):
┌──────────────────────────────┐
│      ★ HEADLINE ★            │  ← Bold, 60px+, text shadow
│      ─── accent line ───     │
│                              │
│    ░░░░  GLOW HALO  ░░░░    │
│    ░░  ╔═══════════╗  ░░    │
│    ░░  ║  PRODUCT   ║  ░░    │  ← 55% height, enhanced, shadow
│    ░░  ╚═══════════╝  ░░    │
│    ░░░░░░░░░░░░░░░░░░░░░    │
│                              │
│      body text (short)       │
│                              │
│   ╔═══════════════════════╗  │
│   ║    CALL TO ACTION     ║  │  ← Full-width rounded button
│   ╚═══════════════════════╝  │
└──────────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    enhance_product, add_drop_shadow, add_glow_behind,
    make_gradient, make_radial_glow, wrap_text, measure_text,
)


# ── Vibrant gradient palettes (bright! never dark/muddy) ──────────────────────
GRADIENTS = {
    "food":      [(255, 130, 67),  (255, 80, 120)],    # warm coral → hot pink
    "fashion":   [(45, 20, 80),    (120, 40, 140)],     # royal purple → violet
    "tech":      [(15, 32, 65),    (30, 80, 160)],      # navy → electric blue
    "services":  [(102, 126, 234), (168, 75, 200)],     # periwinkle → purple
    "wellness":  [(34, 139, 87),   (102, 205, 170)],    # forest → mint
    "beauty":    [(220, 80, 140),  (250, 150, 180)],    # magenta → rose
    "beverage":  [(255, 107, 53),  (255, 195, 113)],    # sunset
    "other":     [(60, 60, 130),   (120, 80, 180)],     # indigo → purple
}

ACCENT_COLORS = {
    "food":      (255, 220, 80),   # golden yellow
    "fashion":   (255, 100, 130),  # coral pink
    "tech":      (0, 200, 255),    # cyan
    "services":  (255, 220, 100),  # gold
    "wellness":  (255, 255, 255),  # white
    "beauty":    (255, 255, 255),  # white
    "beverage":  (255, 255, 255),  # white
    "other":     (255, 210, 80),   # gold
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Hero Center ad poster — market-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 210, 80))

    # ── Build canvas with smoothstep gradient ─────────────────────────────────
    canvas = make_gradient((W, H), grad_top, grad_bot).convert("RGBA")

    # ── Radial glow in center (adds depth) ────────────────────────────────────
    bright_center = tuple(min(255, c + 60) for c in grad_top)
    glow = make_radial_glow((W, H), (cx, int(H * 0.45)), bright_center, int(min(W, H) * 0.45), opacity=50)
    canvas = Image.alpha_composite(canvas, glow)

    # ── Subtle dot pattern overlay for texture ────────────────────────────────
    pattern = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(pattern)
    for y in range(0, H, 40):
        for x in range(0, W, 40):
            p_draw.ellipse([x, y, x + 2, y + 2], fill=(255, 255, 255, 12))
    canvas = Image.alpha_composite(canvas, pattern)

    draw = ImageDraw.Draw(canvas)
    rtl = is_rtl(language)

    # ══════════════════════════════════════════════════════════════════════════
    # HEADLINE — Large, bold, with text shadow
    # ══════════════════════════════════════════════════════════════════════════
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(58, W // 14)  # Much larger than before
    h_font = get_font(language, size=h_size, bold=True)

    max_text_w = int(W * 0.85)
    wrapped_h = wrap_text(draw, headline, h_font, max_text_w)
    h_bbox_full = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox_full[2] - h_bbox_full[0]
    total_hh = h_bbox_full[3] - h_bbox_full[1]

    h_x = cx - hw // 2
    h_y = int(H * 0.05)

    draw.multiline_text((h_x, h_y), wrapped_h, font=h_font, fill=(255, 255, 255), align="center")

    y_cursor = h_y + total_hh + int(H * 0.02)

    # ── Accent line under headline ────────────────────────────────────────────
    line_w = min(hw, int(W * 0.25))
    draw.rounded_rectangle(
        [cx - line_w // 2, y_cursor, cx + line_w // 2, y_cursor + 4],
        radius=2, fill=accent,
    )
    y_cursor += int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # PRODUCT IMAGE — Large, enhanced, with glow + shadow
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")

    # Auto-enhance dark products
    product = enhance_product(product, target_brightness=1.4)

    # Scale product to fill 55% of remaining space
    remaining_h = H - y_cursor - int(H * 0.22)  # leave room for body + CTA
    product_zone_h = max(int(remaining_h * 0.85), int(H * 0.35))
    product_zone_w = int(W * 0.75)

    product.thumbnail((product_zone_w, product_zone_h), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = y_cursor + (remaining_h - ph) // 4  # slightly above center of zone

    # White glow behind product (makes it POP)
    canvas = add_glow_behind(canvas, product, (px, py),
                             glow_color=(255, 255, 255), glow_opacity=40,
                             glow_radius=50, glow_scale=1.25)

    # Drop shadow
    canvas = add_drop_shadow(canvas, product, (px, py),
                             shadow_opacity=120, shadow_offset=(0, 18), blur_radius=35)

    draw = ImageDraw.Draw(canvas)
    y_cursor = py + ph + int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # BODY TEXT — Short tagline
    # ══════════════════════════════════════════════════════════════════════════
    body = prepare_text(safe_get(copy, "body")[:100], language)
    b_size = max(28, W // 28)
    b_font = get_font(language, size=b_size)

    wrapped_body = wrap_text(draw, body, b_font, int(W * 0.80))
    b_bbox_full = draw.multiline_textbbox((0, 0), wrapped_body, font=b_font)
    bw = b_bbox_full[2] - b_bbox_full[0]
    total_bh = b_bbox_full[3] - b_bbox_full[1]
    b_x = cx - bw // 2

    draw.multiline_text((b_x, y_cursor), wrapped_body, font=b_font, fill=(230, 230, 235), align="center")

    y_cursor += total_bh + int(H * 0.025)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA BUTTON — Wide, rounded, prominent
    # ══════════════════════════════════════════════════════════════════════════
    cta_text = prepare_text(safe_get(copy, "cta", "Get Yours Now →"), language)
    cta_size = max(34, W // 26)
    cta_font = get_font(language, size=cta_size, bold=True)

    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_tw = cta_bbox[2] - cta_bbox[0]
    cta_th = cta_bbox[3] - cta_bbox[1]

    pad_x, pad_y = 60, 22
    btn_w = max(cta_tw + pad_x * 2, int(W * 0.55))  # Minimum 55% width
    btn_h = cta_th + pad_y * 2
    btn_x = cx - btn_w // 2
    btn_y = min(y_cursor, H - btn_h - int(H * 0.04))  # Don't go below canvas

    # Button shadow
    shadow_rect = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_rect)
    s_draw.rounded_rectangle([btn_x + 3, btn_y + 5, btn_x + btn_w + 3, btn_y + btn_h + 5],
                              radius=btn_h // 2, fill=(0, 0, 0, 80))
    shadow_rect = shadow_rect.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = Image.alpha_composite(canvas, shadow_rect)
    draw = ImageDraw.Draw(canvas)

    # Button fill
    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                            radius=btn_h // 2, fill=accent)

    # Button text (auto contrast)
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_color = (20, 20, 20) if brightness > 128 else (255, 255, 255)

    tx = cx - cta_tw // 2
    ty = btn_y + pad_y
    draw.text((tx, ty), cta_text, font=cta_font, fill=btn_text_color)

    # ── Final output ──────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=93)
    return buf.getvalue()
