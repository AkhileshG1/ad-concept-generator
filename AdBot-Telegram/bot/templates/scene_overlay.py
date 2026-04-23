"""bot/templates/scene_overlay.py — Full-bleed scene overlay template.

Used when: No product photo is uploaded → Pollinations AI generates a full
scene/background image → we composite professional typography on top.

This is the "no-product-photo" path. The generated image fills the canvas
completely, then we apply:
  1. Intelligent dark gradient overlay (bottom 50%) for text readability
  2. Optional top luminous overlay for brand feel
  3. Frosted glass headline panel
  4. Full body text (properly wrapped, not truncated)
  5. Premium CTA pill button
  6. Hashtag strip
  7. Accent bar at top

This ensures the Pollinations pipeline NEVER sends raw/unbranded images.
Every output looks professional regardless of image source.

Layout:
  ┌──────────────────────────────────────────┐
  │ ▓▓▓▓ accent bar ▓▓▓▓                     │
  │                                          │
  │    [  AI Scene Image — Full Bleed   ]    │
  │    [  fills entire canvas           ]    │
  │    [  with top overlay              ]    │
  │                                          │
  │ ░░░░░░ gradient darkens bottom ░░░░░░░░ │
  │                                          │
  │  ╔══════════════════════════════════╗   │
  │  ║   HEADLINE (frosted glass)       ║   │
  │  ║   body text (full, no cutoff)    ║   │
  │  ╚══════════════════════════════════╝   │
  │                                          │
  │   ╔════════════════════════════╗        │
  │   ║      CALL TO ACTION        ║        │
  │   ╚════════════════════════════╝        │
  │  #tag #tag #tag                          │
  └──────────────────────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get
from bot.templates._effects import (
    make_gradient, add_frosted_glass_panel,
    draw_text_with_shadow, wrap_text, measure_text,
    add_dot_pattern, add_vignette,
)

# Accent colours per business type for the overlay
ACCENT_COLORS = {
    "food":      (255, 220, 70),
    "fashion":   (255, 120, 155),
    "tech":      (0, 200, 255),
    "services":  (255, 215, 80),
    "wellness":  (120, 255, 180),
    "beauty":    (255, 200, 220),
    "beverage":  (255, 220, 80),
    "other":     (255, 215, 70),
}

# Dark overlay colours per business type (bottom gradient)
OVERLAY_COLORS = {
    "food":      (30, 10, 5),
    "fashion":   (10, 5, 25),
    "tech":      (5, 10, 30),
    "services":  (15, 15, 50),
    "wellness":  (5, 25, 15),
    "beauty":    (30, 5, 20),
    "beverage":  (25, 10, 0),
    "other":     (10, 10, 30),
}


def compose(
    scene_image_bytes: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "other",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    """
    Composite professional ad typography over a full-scene AI-generated image.

    Args:
        scene_image_bytes : Raw bytes of the Pollinations/AI-generated scene image
        copy              : Gemini copy dict {headline, body, cta, hashtags, ...}
        platform          : instagram | poster | whatsapp
        business_type     : Used for accent/overlay colour selection
        language          : ISO 639-1 code for font selection
        brand_color       : Optional (R,G,B) accent override
    """
    sizes = {
        "instagram": (1080, 1080),
        "poster":    (1080, 1350),
        "whatsapp":  (800, 800),
    }
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "other").lower()
    accent = brand_color or ACCENT_COLORS.get(biz, (255, 215, 70))
    overlay_dark = OVERLAY_COLORS.get(biz, (10, 10, 30))

    # ── 1. Load & crop scene image to fill canvas (smart crop centre) ──────────
    try:
        scene = Image.open(io.BytesIO(scene_image_bytes)).convert("RGB")
    except Exception:
        # Fallback: solid background if image is corrupt
        scene = Image.new("RGB", (W, H), overlay_dark)

    # Smart centre-crop to target aspect ratio
    sw, sh = scene.size
    target_ratio = W / H
    source_ratio = sw / sh

    if source_ratio > target_ratio:
        # Image is wider — crop width
        new_w = int(sh * target_ratio)
        left = (sw - new_w) // 2
        scene = scene.crop((left, 0, left + new_w, sh))
    elif source_ratio < target_ratio:
        # Image is taller — crop height
        new_h = int(sw / target_ratio)
        top = (sh - new_h) // 2
        scene = scene.crop((0, top, sw, top + new_h))

    canvas = scene.resize((W, H), Image.LANCZOS).convert("RGBA")

    # ── 2. Top luminous overlay (brand feel, subtle) ───────────────────────────
    top_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tg_draw = ImageDraw.Draw(top_glow)
    for y in range(int(H * 0.30)):
        t = y / (H * 0.30)
        alpha = int(50 * (1 - t))  # fades to transparent
        tg_draw.line([(0, y), (W, y)], fill=(*accent[:3], alpha))
    canvas = Image.alpha_composite(canvas, top_glow)

    # ── 3. Strong dark gradient in bottom 55% (text readability) ──────────────
    dark_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    do_draw = ImageDraw.Draw(dark_overlay)
    overlay_start = int(H * 0.38)
    for y in range(overlay_start, H):
        t = (y - overlay_start) / (H - overlay_start)
        t = t * t * (3 - 2 * t)  # smoothstep
        alpha = int(200 * t)
        col = tuple(int(overlay_dark[i] * t) for i in range(3))
        do_draw.line([(0, y), (W, y)], fill=(*col, alpha))
    canvas = Image.alpha_composite(canvas, dark_overlay)

    # ── 4. Vignette ────────────────────────────────────────────────────────────
    canvas = add_vignette(canvas, strength=45)

    draw = ImageDraw.Draw(canvas)

    # ── 5. Accent top bar ──────────────────────────────────────────────────────
    bar_h = max(5, H // 200)
    bar_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(bar_layer)
    b_draw.rectangle([0, 0, W, bar_h], fill=(*accent[:3], 220))
    canvas = Image.alpha_composite(canvas, bar_layer)
    draw = ImageDraw.Draw(canvas)

    # Business type label top-right
    cat_size = max(18, W // 52)
    cat_font = get_font(language, size=cat_size, bold=True)
    cat_text = (biz or "AD").upper()
    cw, ch = measure_text(draw, cat_text, cat_font)
    draw.text(
        (W - cw - int(W * 0.04), bar_h + int(H * 0.012)),
        cat_text, font=cat_font, fill=(*accent[:3], 200)
    )

    # ══════════════════════════════════════════════════════════════════════════
    # TEXT ZONE — starts at 42% down, sits on dark overlay
    # ══════════════════════════════════════════════════════════════════════════
    text_y = int(H * 0.42)

    # ── Headline (frosted glass panel) ─────────────────────────────────────────
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_size = max(58, W // 14)
    h_font = get_font(language, size=h_size, bold=True)

    max_text_w = int(W * 0.86)
    wrapped_h = wrap_text(draw, headline, h_font, max_text_w)
    h_bbox = draw.multiline_textbbox((0, 0), wrapped_h, font=h_font)
    hw = h_bbox[2] - h_bbox[0]
    hh = h_bbox[3] - h_bbox[1]
    h_x = cx - hw // 2

    canvas = draw_text_with_shadow(
        canvas, (h_x, text_y), wrapped_h, h_font,
        fill=(255, 255, 255),
        shadow_color=(0, 0, 0),
        shadow_offset=4, shadow_blur=14,
        multiline=True,
    )
    draw = ImageDraw.Draw(canvas)
    text_y += hh + int(H * 0.016)

    # Accent underline
    line_w = min(hw, int(W * 0.22))
    draw.rounded_rectangle(
        [cx - line_w // 2, text_y, cx + line_w // 2, text_y + 5],
        radius=3, fill=accent[:3]
    )
    text_y += int(H * 0.028)

    # ── Body text — FULL TEXT, properly wrapped, no truncation ────────────────
    body_raw = safe_get(copy, "body", "")
    # Allow full body up to 200 chars (properly wrapped in panel)
    body = prepare_text(body_raw[:200], language)
    b_size = max(27, W // 27)
    b_font = get_font(language, size=b_size)

    wrapped_body = wrap_text(draw, body, b_font, int(W * 0.78))
    b_bbox = draw.multiline_textbbox((0, 0), wrapped_body, font=b_font)
    bw = b_bbox[2] - b_bbox[0]
    bh = b_bbox[3] - b_bbox[1]

    # Frosted glass panel for body
    pad_panel = int(W * 0.04)
    panel_x1 = int(W * 0.07)
    panel_x2 = W - int(W * 0.07)
    panel_y1 = text_y
    panel_y2 = text_y + bh + pad_panel * 2

    cta_space = int(H * 0.13)  # reserve space for CTA button
    if panel_y2 < H - cta_space and body:
        canvas = add_frosted_glass_panel(
            canvas, (panel_x1, panel_y1, panel_x2, panel_y2),
            color=(255, 255, 255), opacity=15, radius=16, border_opacity=45
        )
        draw = ImageDraw.Draw(canvas)
        b_x = cx - bw // 2
        draw.multiline_text(
            (b_x, panel_y1 + pad_panel),
            wrapped_body, font=b_font,
            fill=(225, 225, 230), align="center"
        )
        text_y = panel_y2 + int(H * 0.024)
    else:
        text_y += int(H * 0.015)

    # ══════════════════════════════════════════════════════════════════════════
    # CTA BUTTON — Premium pill, gradient fill
    # ══════════════════════════════════════════════════════════════════════════
    cta_text = prepare_text(safe_get(copy, "cta", "Get Yours Now →"), language)
    cta_size = max(34, W // 24)
    cta_font = get_font(language, size=cta_size, bold=True)

    cta_bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    cta_tw = cta_bbox[2] - cta_bbox[0]
    cta_th = cta_bbox[3] - cta_bbox[1]

    pad_x, pad_y = 60, 22
    btn_w = max(cta_tw + pad_x * 2, int(W * 0.58))
    btn_h = cta_th + pad_y * 2
    btn_x = cx - btn_w // 2
    btn_y = min(text_y, H - btn_h - int(H * 0.042))

    # Button shadow
    shad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2 = ImageDraw.Draw(shad)
    s2.rounded_rectangle(
        [btn_x + 4, btn_y + 8, btn_x + btn_w + 4, btn_y + btn_h + 8],
        radius=btn_h // 2, fill=(0, 0, 0, 100)
    )
    shad = shad.filter(ImageFilter.GaussianBlur(radius=12))
    canvas = Image.alpha_composite(canvas, shad)
    draw = ImageDraw.Draw(canvas)

    # Gradient button (lighter top → darker base)
    btn_img = make_gradient(
        (btn_w, btn_h),
        tuple(min(255, c + 35) for c in accent[:3]),
        tuple(max(0, c - 25) for c in accent[:3]),
    )
    btn_rgba = btn_img.convert("RGBA")
    mask = Image.new("L", (btn_w, btn_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, btn_w, btn_h], radius=btn_h // 2, fill=235
    )
    btn_rgba.putalpha(mask)
    canvas.paste(btn_rgba, (btn_x, btn_y), btn_rgba)
    draw = ImageDraw.Draw(canvas)

    # Button text — auto colour contrast
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_col = (15, 15, 15) if brightness > 130 else (255, 255, 255)
    draw.text((cx - cta_tw // 2, btn_y + pad_y), cta_text, font=cta_font, fill=btn_text_col)

    # ── Hashtag strip at very bottom ───────────────────────────────────────────
    tags = copy.get("hashtags", [])
    if tags:
        tag_str = "  ".join(
            f"#{t}" if not str(t).startswith("#") else str(t)
            for t in tags[:4]
        )
        tag_size = max(16, W // 62)
        tag_font = get_font(language, size=tag_size)
        tw2, th2 = measure_text(draw, tag_str, tag_font)
        tag_y = H - int(H * 0.028)
        if tag_y + th2 < H:
            draw.text(
                (cx - tw2 // 2, tag_y),
                tag_str, font=tag_font,
                fill=(*accent[:3], 160)
            )

    # ── Final output ───────────────────────────────────────────────────────────
    final = canvas.convert("RGB")
    buf = io.BytesIO()
    final.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()
