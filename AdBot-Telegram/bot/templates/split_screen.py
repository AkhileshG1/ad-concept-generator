"""bot/templates/split_screen.py — Split Screen ad template (v2 AGENCY GRADE).

Best for: Fashion, retail, e-commerce, clothing.

Layout (Instagram 1080×1080):
  ┌────────────────────────┬──────────────────┐
  │                        │ [CATEGORY BADGE] │
  │   ░░ PRODUCT GLOW ░░  │  ──────────────  │
  │   ░░  [ PRODUCT ]  ░░  │  HEADLINE BOLD   │
  │   ░░    shadow     ░░  │  ─────────────── │
  │   [ floor reflect ]    │  body text       │
  │                        │                  │
  │  ◈ diagonal accent◈   │  [ CTA BUTTON ]  │
  │                        │  #tag  #tag      │
  └────────────────────────┴──────────────────┘
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


GRADIENTS = {
    "food":      [(230, 80, 30),   (190, 30, 80)],
    "fashion":   [(18, 10, 42),    (45, 18, 80)],
    "tech":      [(10, 18, 45),    (22, 48, 100)],
    "services":  [(55, 80, 190),   (90, 50, 160)],
    "wellness":  [(20, 100, 60),   (50, 160, 100)],
    "beauty":    [(160, 30, 90),   (210, 90, 145)],
    "retail":    [(35, 25, 65),    (70, 42, 115)],
    "clothing":  [(25, 15, 45),    (55, 28, 80)],
    "other":     [(40, 30, 80),    (75, 52, 130)],
}

RIGHT_BG = {
    "food":      [(245, 230, 215), (255, 245, 235)],
    "fashion":   [(248, 244, 255), (238, 232, 252)],
    "tech":      [(240, 244, 252), (228, 236, 250)],
    "services":  [(240, 242, 255), (228, 232, 252)],
    "wellness":  [(238, 252, 244), (225, 245, 234)],
    "beauty":    [(255, 240, 248), (252, 228, 240)],
    "retail":    [(248, 244, 255), (235, 230, 252)],
    "clothing":  [(248, 244, 255), (235, 230, 252)],
    "other":     [(245, 242, 255), (232, 228, 252)],
}

ACCENT_COLORS = {
    "food":      (255, 200, 50),
    "fashion":   (255, 110, 145),
    "tech":      (0, 200, 255),
    "services":  (255, 195, 70),
    "wellness":  (80, 230, 140),
    "beauty":    (255, 195, 220),
    "retail":    (255, 175, 70),
    "clothing":  (255, 130, 100),
    "other":     (255, 200, 90),
}

TEXT_COLORS = {
    "food":      (60, 20, 10),
    "fashion":   (30, 18, 60),
    "tech":      (20, 30, 75),
    "services":  (25, 30, 90),
    "wellness":  (15, 60, 35),
    "beauty":    (80, 15, 50),
    "retail":    (30, 20, 65),
    "clothing":  (25, 15, 55),
    "other":     (30, 25, 70),
}


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """Render a Split Screen ad — agency-grade quality."""

    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800,  800),
    }
    W, H = sizes.get(platform, (1080, 1080))

    biz = (business_type or "other").lower()
    grad_top, grad_bot = GRADIENTS.get(biz, GRADIENTS["other"])
    rt, rb = RIGHT_BG.get(biz, RIGHT_BG["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 200, 90))
    text_col = TEXT_COLORS.get(biz, (30, 25, 70))

    # ── Layout ────────────────────────────────────────────────────────────────
    split_x = int(W * 0.54)
    text_zone_x = split_x + 16
    text_zone_w = W - text_zone_x - int(W * 0.035)

    # ── Canvas: two panel gradients ───────────────────────────────────────────
    canvas = Image.new("RGB", (W, H))
    left_panel = make_gradient((split_x, H), grad_top, grad_bot)
    canvas.paste(left_panel, (0, 0))
    right_panel = make_gradient((W - split_x, H), rt, rb)
    canvas.paste(right_panel, (split_x, 0))
    canvas = canvas.convert("RGBA")

    # Left panel: dot texture
    left_dot = add_dot_pattern(
        Image.new("RGBA", (split_x, H), (0, 0, 0, 0)),
        spacing=38, dot_size=2, opacity=14
    )
    canvas.paste(left_dot, (0, 0), left_dot)

    # ── Diagonal accent stripe between panels ─────────────────────────────────
    stripe_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(stripe_layer)
    # Angled stripe: slightly diagonal
    slant = int(H * 0.04)
    pts = [
        (split_x - 8, 0),
        (split_x + 8, 0),
        (split_x + 8 + slant, H),
        (split_x - 8 + slant, H),
    ]
    s_draw.polygon(pts, fill=(*accent[:3], 180))
    stripe_layer = stripe_layer.filter(ImageFilter.GaussianBlur(radius=2))
    canvas = Image.alpha_composite(canvas, stripe_layer)

    # ── Left panel radial glow (behind product) ───────────────────────────────
    center_lx = split_x // 2
    center_ly = H // 2
    glow_overlay = make_radial_glow(
        (W, H), (center_lx, center_ly),
        tuple(min(255, c + 70) for c in grad_top),
        int(min(split_x, H) * 0.45), opacity=55
    )
    canvas = Image.alpha_composite(canvas, glow_overlay)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # LEFT PANEL — Product image
    # ══════════════════════════════════════════════════════════════════════════
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    product = enhance_product(product, target_brightness=1.50)

    prod_max_w = int(split_x * 0.88)
    prod_max_h = int(H * 0.72)
    product.thumbnail((prod_max_w, prod_max_h), Image.LANCZOS)
    pw, ph = product.size

    px = (split_x - pw) // 2
    py = (H - ph) // 2

    # Accent-coloured glow behind product
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=tuple(min(255, c + 80) for c in accent[:3]),
        glow_opacity=55, glow_radius=75, glow_scale=1.35
    )
    # White inner halo
    canvas = add_glow_behind(
        canvas, product, (px, py),
        glow_color=(255, 255, 255), glow_opacity=28,
        glow_radius=30, glow_scale=1.10
    )
    canvas = add_drop_shadow(
        canvas, product, (px, py),
        shadow_opacity=130, shadow_offset=(10, 18), blur_radius=35
    )
    canvas = add_product_reflection(canvas, product, (px, py), opacity=35, height_fraction=0.18)

    draw = ImageDraw.Draw(canvas)

    # ══════════════════════════════════════════════════════════════════════════
    # RIGHT PANEL — Text
    # ══════════════════════════════════════════════════════════════════════════
    text_x = text_zone_x + int(W * 0.018)
    cy = int(H * 0.10)

    # Category badge (pill)
    cat_size = max(20, W // 46)
    cat_font = get_font(language, size=cat_size, bold=True)
    cat_text = prepare_text((biz or "AD").upper(), language)
    cw, ch = measure_text(draw, cat_text, cat_font)
    badge_px, badge_py = 16, 7
    badge_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge_layer)
    b_draw.rounded_rectangle(
        [text_x, cy, text_x + cw + badge_px * 2, cy + ch + badge_py * 2],
        radius=(ch + badge_py * 2) // 2, fill=(*accent[:3], 210)
    )
    canvas = Image.alpha_composite(canvas, badge_layer)
    draw = ImageDraw.Draw(canvas)
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    badge_text_col = (15, 15, 15) if brightness > 130 else (255, 255, 255)
    draw.text((text_x + badge_px, cy + badge_py), cat_text, font=cat_font, fill=badge_text_col)
    cy += ch + badge_py * 2 + int(H * 0.025)

    # Accent divider
    draw.rectangle([text_x, cy, text_x + int(text_zone_w * 0.40), cy + 4], fill=accent[:3])
    cy += int(H * 0.030)

    # Headline
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(46, W // 19)
    h_font = get_font(language, size=h_size, bold=True)
    wrapped_h = wrap_text(draw, headline, h_font, text_zone_w)
    h_bbox = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    total_hh = h_bbox[3] - h_bbox[1]

    canvas = draw_text_with_shadow(
        canvas, (text_x, cy), wrapped_h, h_font,
        fill=text_col, shadow_color=(200, 200, 220),
        shadow_offset=2, shadow_blur=5, multiline=True
    )
    draw = ImageDraw.Draw(canvas)
    cy += total_hh + int(H * 0.022)

    # Body text
    body = prepare_text(safe_get(copy, "body", "")[:140], language)
    b_size = max(24, W // 36)
    b_font = get_font(language, size=b_size)
    wrapped_b = wrap_text(draw, body, b_font, text_zone_w - 10)
    b_bbox = draw.multiline_textbbox((0, 0), wrapped_b, font=b_font)
    total_bh = b_bbox[3] - b_bbox[1]

    draw.multiline_text((text_x, cy), wrapped_b, font=b_font,
                         fill=(*text_col[:3], 200), align="left")
    cy += total_bh + int(H * 0.038)

    # CTA button (right panel width)
    cta = prepare_text(safe_get(copy, "cta", "Shop Now →"), language)
    cta_size = max(30, W // 30)
    cta_font = get_font(language, size=cta_size, bold=True)
    ct_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_tw = ct_bbox[2] - ct_bbox[0]
    cta_th = ct_bbox[3] - ct_bbox[1]

    pad_x, pad_y = 36, 18
    btn_w = max(cta_tw + pad_x * 2, int(text_zone_w * 0.85))
    btn_h = cta_th + pad_y * 2
    btn_x = text_x
    btn_y = min(cy, H - btn_h - int(H * 0.055))

    # Button shadow
    shad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2 = ImageDraw.Draw(shad)
    s2.rounded_rectangle(
        [btn_x + 3, btn_y + 6, btn_x + btn_w + 3, btn_y + btn_h + 6],
        radius=btn_h // 2, fill=(0, 0, 0, 60)
    )
    shad = shad.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = Image.alpha_composite(canvas, shad)
    draw = ImageDraw.Draw(canvas)

    btn_img = make_gradient(
        (btn_w, btn_h),
        tuple(min(255, c + 30) for c in accent[:3]),
        tuple(max(0, c - 15)  for c in accent[:3]),
    )
    btn_rgba = btn_img.convert("RGBA")
    mask = Image.new("L", (btn_w, btn_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, btn_w, btn_h], radius=btn_h // 2, fill=230)
    btn_rgba.putalpha(mask)
    canvas.paste(btn_rgba, (btn_x, btn_y), btn_rgba)
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (btn_x + (btn_w - cta_tw) // 2, btn_y + pad_y),
        cta, font=cta_font, fill=badge_text_col
    )

    # Hashtags under button
    tags = copy.get("hashtags", [])
    if tags:
        tag_str = " ".join(f"#{t}" if not t.startswith("#") else t for t in tags[:3])
        tag_size = max(16, W // 64)
        tag_font = get_font(language, size=tag_size)
        tag_y = btn_y + btn_h + int(H * 0.018)
        if tag_y < H - int(H * 0.02):
            draw.text((text_x, tag_y), tag_str, font=tag_font,
                      fill=(*accent[:3], 160))

    # ── Final output ───────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()
