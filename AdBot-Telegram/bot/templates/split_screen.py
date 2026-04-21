"""bot/templates/split_screen.py — Split Screen ad template (v2 PRO).

Best for: Fashion, retail, e-commerce, clothing.
Layout: Product on LEFT (60%), text + CTA on RIGHT (40%).

Design philosophy:
  - Product dominates the left side (hero treatment)
  - Clean text column on right with clear hierarchy
  - Large headline, body, and prominent CTA
  - Accent stripe separating the two halves
  - Auto-brightness for dark product photos

Canvas (default 1080×1080):
┌──────────────────────┬──────────────┐
│                      │ accent stripe│
│                      │              │
│                      │  CATEGORY    │
│   [  PRODUCT PNG  ]  │  ─────────   │
│   (60% width)        │  HEADLINE    │
│   enhanced + shadow  │              │
│                      │  body text   │
│                      │              │
│                      │  [ CTA BTN ] │
│                      │              │
└──────────────────────┴──────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    enhance_product, add_drop_shadow, make_gradient,
    wrap_text, measure_text,
)


GRADIENTS = {
    "food":      [(255, 107, 53),  (255, 140, 80)],
    "fashion":   [(35, 25, 55),    (55, 35, 85)],
    "tech":      [(18, 28, 50),    (28, 50, 90)],
    "services":  [(70, 90, 180),   (100, 60, 160)],
    "wellness":  [(40, 120, 80),   (60, 160, 100)],
    "beauty":    [(180, 50, 110),  (220, 100, 150)],
    "retail":    [(40, 30, 70),    (80, 50, 120)],
    "clothing":  [(30, 20, 50),    (60, 30, 80)],
    "other":     [(50, 40, 80),    (80, 60, 120)],
}

ACCENT_COLORS = {
    "food":      (255, 200, 60),
    "fashion":   (255, 100, 130),
    "tech":      (0, 180, 255),
    "services":  (255, 200, 80),
    "wellness":  (120, 255, 160),
    "beauty":    (255, 200, 220),
    "retail":    (255, 180, 80),
    "clothing":  (255, 130, 100),
    "other":     (255, 200, 100),
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Split Screen ad poster — market-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))

    biz = (business_type or "other").lower()
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 200, 100))

    # ── Layout split ──────────────────────────────────────────────────────────
    split_x = int(W * 0.55)        # Product side = 55%
    text_zone_x = split_x + 12     # After accent stripe
    text_zone_w = W - text_zone_x - int(W * 0.04)  # Right padding

    # ── Canvas — slightly lighter gradient for the right panel ────────────────
    canvas = Image.new("RGB", (W, H))

    # Left panel: darker gradient (product backdrop)
    left_panel = make_gradient((split_x, H), grad_top, grad_bot)
    canvas.paste(left_panel, (0, 0))

    # Right panel: slightly lighter
    right_top = tuple(min(255, c + 15) for c in grad_top)
    right_bot = tuple(min(255, c + 10) for c in grad_bot)
    right_panel = make_gradient((W - split_x, H), right_top, right_bot)
    canvas.paste(right_panel, (split_x, 0))

    canvas = canvas.convert("RGBA")

    # ── Accent stripe between panels ──────────────────────────────────────────
    stripe = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stripe)
    stripe_w = 5
    s_draw.rectangle([split_x - stripe_w // 2, 0, split_x + stripe_w // 2, H],
                      fill=accent + (180,))
    canvas = Image.alpha_composite(canvas, stripe)

    draw = ImageDraw.Draw(canvas)
    rtl = is_rtl(language)

    # ══════════════════════════════════════════════════════════════════════════
    # LEFT PANEL — Product image (enhanced, with shadow)
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.5)

    # Scale product to fill left panel (85% of panel width, 70% of height)
    prod_max_w = int(split_x * 0.85)
    prod_max_h = int(H * 0.70)
    product.thumbnail((prod_max_w, prod_max_h), Image.LANCZOS)
    pw, ph = product.size

    # Center product in left panel
    px = (split_x - pw) // 2
    py = (H - ph) // 2

    # Subtle glow behind product
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_layer)
    glow_r = max(pw, ph) // 2 + 40
    g_center_x = px + pw // 2
    g_center_y = py + ph // 2
    g_draw.ellipse([g_center_x - glow_r, g_center_y - glow_r,
                     g_center_x + glow_r, g_center_y + glow_r],
                    fill=(255, 255, 255, 30))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=50))
    canvas = Image.alpha_composite(canvas, glow_layer)

    # Drop shadow + paste product
    canvas = add_drop_shadow(canvas, product, (px, py),
                             shadow_opacity=100, shadow_offset=(8, 14), blur_radius=25)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT PANEL — Text content
    # ══════════════════════════════════════════════════════════════════════════
    text_x = text_zone_x + int(W * 0.02)
    cy = int(H * 0.12)  # Start text lower for breathing space

    # ── Category label (small, accent colored) ────────────────────────────────
    cat_font = get_font(language, size=max(22, W // 42), bold=True)
    cat_text = prepare_text((biz or "AD").upper(), language)
    draw.text((text_x, cy), cat_text, font=cat_font, fill=accent)
    cy += int(H * 0.045)

    # ── Small accent line ─────────────────────────────────────────────────────
    draw.rectangle([text_x, cy, text_x + int(text_zone_w * 0.35), cy + 3], fill=accent)
    cy += int(H * 0.035)

    # ── Headline (large, bold) ────────────────────────────────────────────────
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(44, W // 20)
    h_font = get_font(language, size=h_size, bold=True)
    wrapped_h = wrap_text(draw, headline, h_font, text_zone_w)
    h_bbox_full = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    total_hh = h_bbox_full[3] - h_bbox_full[1]

    draw.multiline_text((text_x, cy), wrapped_h, font=h_font, fill=(255, 255, 255))
    cy += total_hh + int(H * 0.03)

    # ── Body text ─────────────────────────────────────────────────────────────
    body = prepare_text(safe_get(copy, "body")[:130], language)
    b_size = max(24, W // 36)
    b_font = get_font(language, size=b_size)
    wrapped_b = wrap_text(draw, body, b_font, text_zone_w)
    b_bbox_full = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
    total_bh = b_bbox_full[3] - b_bbox_full[1]

    draw.multiline_text((text_x, cy), wrapped_b, font=b_font, fill=(200, 200, 210))
    cy += total_bh + int(H * 0.04)

    # ── CTA button ────────────────────────────────────────────────────────────
    cta = prepare_text(safe_get(copy, "cta", "Shop Now →"), language)
    cta_size = max(30, W // 30)
    cta_font = get_font(language, size=cta_size, bold=True)
    ct_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_tw = ct_bbox[2] - ct_bbox[0]
    cta_th = ct_bbox[3] - ct_bbox[1]

    pad_x, pad_y = 40, 18
    btn_w = max(cta_tw + pad_x * 2, int(text_zone_w * 0.80))
    btn_h = cta_th + pad_y * 2
    btn_x = text_x
    btn_y = min(cy, H - btn_h - int(H * 0.06))

    # Button shadow
    shadow_btn = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sb_draw = ImageDraw.Draw(shadow_btn)
    sb_draw.rounded_rectangle([btn_x + 3, btn_y + 4, btn_x + btn_w + 3, btn_y + btn_h + 4],
                               radius=btn_h // 2, fill=(0, 0, 0, 70))
    shadow_btn = shadow_btn.filter(ImageFilter.GaussianBlur(radius=6))
    canvas = Image.alpha_composite(canvas, shadow_btn)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle([btn_x, btn_y, btn_x + btn_w, btn_y + btn_h],
                            radius=btn_h // 2, fill=accent)

    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_color = (20, 20, 20) if brightness > 128 else (255, 255, 255)

    tx = btn_x + (btn_w - cta_tw) // 2
    ty = btn_y + pad_y
    draw.text((tx, ty), cta, font=cta_font, fill=btn_text_color)

    # ── Final output ──────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=93)
    return buf.getvalue()
