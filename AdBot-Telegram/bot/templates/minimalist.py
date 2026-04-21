"""bot/templates/minimalist.py — Minimalist dark ad template.

Best for: Tech, SaaS, premium products, electronics.
Layout: Dark gradient, product centered with glow, clean type below.

Canvas:
┌────────────────────────┐
│  (very dark gradient)  │
│                        │
│      [Product PNG]     │
│     ✦ glow effect ✦    │
│                        │
│  HEADLINE (large)      │
│  tagline (small)       │
│                        │
│  [ → CTA ]             │
└────────────────────────┘
"""
import io
import math
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl
from bot.templates._utils import safe_get


DARK_GRADIENTS = {
    "tech":      [(8,   12,  20),  (18, 26,  40)],
    "fashion":   [(10,  10,  18),  (25, 15,  35)],
    "services":  [(12,  12,  25),  (25, 20,  50)],
    "other":     [(10,  10,  18),  (20, 20,  35)],
}

GLOW_COLORS = {
    "tech":      (40, 100, 255),
    "fashion":   (180, 30, 100),
    "services":  (100, 60, 200),
    "other":     (60,  80, 200),
}

ACCENT_COLORS = {
    "tech":      (88,  166, 255),
    "fashion":   (233, 69,  96),
    "services":  (150, 100, 255),
    "other":     (100, 180, 255),
}


def _make_gradient(size, top, bottom):
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
    business_type: str = "tech",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    sizes = {"instagram": (1080, 1080), "poster": (1080, 1350), "whatsapp": (800, 800)}
    W, H = sizes.get(platform, (1080, 1080))
    cx = W // 2

    biz = (business_type or "tech").lower()
    grad_top, grad_bot = DARK_GRADIENTS.get(biz, DARK_GRADIENTS["other"])
    glow_color = GLOW_COLORS.get(biz, GLOW_COLORS["other"])
    accent = brand_color or ACCENT_COLORS.get(biz, (88, 166, 255))
    rtl = is_rtl(language)

    canvas = _make_gradient((W, H), grad_top, grad_bot).convert("RGBA")

    # ── Radial glow in upper center ───────────────────────────────────────────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gr = int(min(W, H) * 0.45)
    gy = int(H * 0.35)
    gd.ellipse([cx - gr, gy - gr, cx + gr, gy + gr], fill=glow_color + (50,))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=90))
    canvas = Image.alpha_composite(canvas, glow)

    # ── Fine dot grid pattern (subtle texture) ────────────────────────────────
    texture = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(texture)
    dot_color = tuple(min(255, c + 25) for c in grad_top) + (30,)
    for xx in range(0, W, 40):
        for yy in range(0, H, 40):
            td.ellipse([xx, yy, xx + 2, yy + 2], fill=dot_color)
    canvas = Image.alpha_composite(canvas, texture)

    draw = ImageDraw.Draw(canvas)

    # ── Product — upper center ─────────────────────────────────────────────────
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    max_pw = int(W * 0.60)
    max_ph = int(H * 0.45)
    product.thumbnail((max_pw, max_ph), Image.LANCZOS)
    pw, ph = product.size
    px = cx - pw // 2
    py = int(H * 0.06)

    # Glow halo behind product
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_color = glow_color + (90,)
    halo_r = max(pw, ph) // 2 + 60
    halo_cx = px + pw // 2
    halo_cy = py + ph // 2
    halo_draw.ellipse([halo_cx - halo_r, halo_cy - halo_r, halo_cx + halo_r, halo_cy + halo_r], fill=halo_color)
    halo = halo.filter(ImageFilter.GaussianBlur(radius=50))
    canvas = Image.alpha_composite(canvas, halo)
    canvas.paste(product, (px, py), product)
    draw = ImageDraw.Draw(canvas)

    y_cursor = py + ph + int(H * 0.04)

    # ── Thin accent line ──────────────────────────────────────────────────────
    line_w = W // 5
    draw.rectangle([cx - line_w // 2, y_cursor, cx + line_w // 2, y_cursor + 2], fill=accent)
    y_cursor += 20

    # ── Headline ──────────────────────────────────────────────────────────────
    headline = prepare_text(safe_get(copy, "headline", "Your Product"), language)
    h_font = get_font(language, size=max(52, W // 16), bold=True)
    wrapped_h = _wrap_text(draw, headline, h_font, int(W * 0.85))
    hbbox = draw.textbbox((0, 0), wrapped_h, font=h_font)
    hw = hbbox[2] - hbbox[0]
    hh = hbbox[3] - hbbox[1]
    n_hl = wrapped_h.count("\n") + 1
    draw.text((cx - hw // 2, y_cursor), wrapped_h, font=h_font, fill=(255, 255, 255), align="center")
    y_cursor += hh * n_hl + 20

    # ── Tagline / body (short) ────────────────────────────────────────────────
    body_short = prepare_text(safe_get(copy, "body")[:90], language)
    b_font = get_font(language, size=max(26, W // 34))
    wrapped_b = _wrap_text(draw, body_short, b_font, int(W * 0.70))
    bbbox = draw.textbbox((0, 0), wrapped_b, font=b_font)
    bw = bbbox[2] - bbbox[0]
    bh = bbbox[3] - bbbox[1]
    n_bl = wrapped_b.count("\n") + 1
    draw.text((cx - bw // 2, y_cursor), wrapped_b, font=b_font, fill=(150, 170, 200), align="center")
    y_cursor += bh * n_bl + 35

    # ── CTA — text with arrow, no filled button (minimalist style) ────────────
    cta = prepare_text(safe_get(copy, "cta", "Learn More →"), language)
    cta_font = get_font(language, size=32, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]
    cta_x = cx - cta_w // 2
    # Underline style button
    draw.text((cta_x, y_cursor), cta, font=cta_font, fill=accent)
    draw.rectangle([cta_x, y_cursor + cta_h + 4, cta_x + cta_w, y_cursor + cta_h + 7], fill=accent)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()
