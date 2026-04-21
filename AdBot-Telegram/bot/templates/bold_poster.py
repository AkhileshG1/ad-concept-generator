"""bot/templates/bold_poster.py — Bold Poster ad template.

Best for: Local services, restaurants, events, promotions, salons.
Layout: Vibrant color block, large headline, bullet benefits, strong CTA.

Canvas:
┌────────────────────────┐
│█ VIBRANT HEADER BLOCK █│
│  BIG BOLD HEADLINE     │
│  ────────────────      │
│    [Product PNG]       │
│  ────────────────      │
│  ✓ Benefit 1           │
│  ✓ Benefit 2           │
│  ✓ Benefit 3           │
│                        │
│  [ BOOK NOW / ORDER ]  │
└────────────────────────┘
"""
import io
from PIL import Image, ImageDraw, ImageFilter
from bot.font_manager import get_font, prepare_text, is_rtl


VIBRANT_PALETTES = {
    "food":      {"header": (220, 50,  50),  "bg": (255, 245, 235), "text": (30, 20, 20),  "accent": (220, 50, 50)},
    "services":  {"header": (41,  98,  255), "bg": (240, 245, 255), "text": (15, 25, 60),  "accent": (41, 98, 255)},
    "wellness":  {"header": (46,  160, 67),  "bg": (240, 255, 244), "text": (15, 50, 20),  "accent": (46, 160, 67)},
    "beauty":    {"header": (200, 30, 120),  "bg": (255, 240, 248), "text": (60, 15, 40),  "accent": (200, 30, 120)},
    "fashion":   {"header": (30,  30,  50),  "bg": (245, 245, 250), "text": (20, 20, 40),  "accent": (200, 50, 80)},
    "education": {"header": (15,  76,  175), "bg": (240, 248, 255), "text": (10, 30, 70),  "accent": (15, 76, 175)},
    "other":     {"header": (60,  90,  200), "bg": (240, 245, 255), "text": (20, 30, 70),  "accent": (60, 90, 200)},
}


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


def _draw_check_items(draw, items, font, x, y, accent, text_color, rtl):
    """Draw a list of bullet/benefit items with checkmarks."""
    check_char = "✓ "
    spacing = 10
    for item in items:
        if not item.strip():
            continue
        full = prepare_text(check_char + item, "en")  # checkmark always LTR
        bbox = draw.textbbox((0, 0), full, font=font)
        h = bbox[3] - bbox[1]

        # Checkmark in accent color
        draw.text((x, y), "✓ ", font=font, fill=accent)
        check_bbox = draw.textbbox((0, 0), "✓ ", font=font)
        check_w = check_bbox[2] - check_bbox[0]

        # Item text
        draw.text((x + check_w, y), item, font=font, fill=text_color)
        y += h + spacing
    return y


def compose(
    product_png: bytes,
    copy: dict,
    platform: str = "instagram",
    business_type: str = "services",
    language: str = "en",
    brand_color: tuple = None,
) -> bytes:
    sizes = {"instagram": (1080, 1080), "poster": (1080, 1350), "whatsapp": (800, 800)}
    W, H = sizes.get(platform, (1080, 1080))

    biz = (business_type or "services").lower()
    palette = VIBRANT_PALETTES.get(biz, VIBRANT_PALETTES["other"])
    if brand_color:
        palette = {**palette, "header": brand_color, "accent": brand_color}

    header_color = palette["header"]
    bg_color = palette["bg"]
    text_color = palette["text"]
    accent = palette["accent"]
    rtl = is_rtl(language)

    canvas = Image.new("RGBA", (W, H), bg_color + (255,))
    draw = ImageDraw.Draw(canvas)

    # ── Header color block (top 22% of canvas) ────────────────────────────────
    header_h = int(H * 0.22)
    draw.rectangle([0, 0, W, header_h], fill=header_color)

    # ── Headline inside header ────────────────────────────────────────────────
    headline = prepare_text(copy.get("headline", ""), language)
    h_font = get_font(language, size=max(52, W // 16), bold=True)
    max_hw = int(W * 0.88)
    wrapped_h = _wrap_text(draw, headline, h_font, max_hw)
    hbbox = draw.textbbox((0, 0), wrapped_h, font=h_font)
    hw = hbbox[2] - hbbox[0]
    hh = hbbox[3] - hbbox[1]
    n_hl = wrapped_h.count("\n") + 1
    total_hh = hh * n_hl
    # Center in header block
    hx = (W - hw) // 2
    hy = (header_h - total_hh) // 2
    # Shadow for readability
    draw.text((hx + 2, hy + 2), wrapped_h, font=h_font, fill=(0, 0, 0, 80))
    draw.text((hx, hy), wrapped_h, font=h_font, fill=(255, 255, 255), align="center")

    # ── Separator line ────────────────────────────────────────────────────────
    sep_y = header_h + 18
    line_w = int(W * 0.60)
    draw.rectangle([(W - line_w) // 2, sep_y, (W + line_w) // 2, sep_y + 4], fill=header_color)

    # ── Product image (center, below header) ──────────────────────────────────
    product = Image.open(io.BytesIO(product_png)).convert("RGBA")
    max_pw = int(W * 0.55)
    max_ph = int(H * 0.32)
    product.thumbnail((max_pw, max_ph), Image.LANCZOS)
    pw, ph = product.size
    px = (W - pw) // 2
    py = header_h + 30

    # Light shadow
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_mask = Image.new("RGBA", product.size, (0, 0, 0, 50))
    if product.mode == "RGBA":
        shadow_mask.putalpha(product.getchannel("A"))
    shadow.paste(shadow_mask, (px + 8, py + 10), shadow_mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=12))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas.paste(product, (px, py), product)
    draw = ImageDraw.Draw(canvas)

    y_cursor = py + ph + 20

    # ── Second separator ──────────────────────────────────────────────────────
    draw.rectangle([(W - line_w) // 2, y_cursor, (W + line_w) // 2, y_cursor + 4], fill=header_color)
    y_cursor += 20

    # ── Bullet benefits (from copy.poster.bullets or parse from body) ─────────
    bullets = []
    poster_data = copy.get("poster", {})
    if poster_data and poster_data.get("bullets"):
        bullets = poster_data["bullets"][:3]
    else:
        # Extract sentences from body as bullets
        body = copy.get("body", "")
        sentences = [s.strip() for s in body.replace(".", ". ").split(". ") if len(s.strip()) > 10]
        bullets = sentences[:3]

    if bullets:
        b_font = get_font(language, size=max(28, W // 30))
        y_cursor = _draw_check_items(draw, bullets, b_font, int(W * 0.12), y_cursor, accent, text_color, rtl)
        y_cursor += 20
    else:
        # Fallback — body text
        body = prepare_text(copy.get("body", "")[:120], language)
        b_font = get_font(language, size=max(28, W // 30))
        wrapped_b = _wrap_text(draw, body, b_font, int(W * 0.80))
        bbbox = draw.textbbox((0, 0), wrapped_b, font=b_font)
        bh = bbbox[3] - bbbox[1]
        n_bl = wrapped_b.count("\n") + 1
        draw.text((int(W * 0.10), y_cursor), wrapped_b, font=b_font, fill=text_color)
        y_cursor += bh * n_bl + 20

    # ── CTA button (full width, bold) ─────────────────────────────────────────
    cta = prepare_text(copy.get("cta", "Order Now"), language)
    cta_font = get_font(language, size=36, bold=True)
    cta_bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cta_w = cta_bbox[2] - cta_bbox[0]
    cta_h = cta_bbox[3] - cta_bbox[1]

    btn_margin = int(W * 0.10)
    btn_x1 = btn_margin
    btn_x2 = W - btn_margin
    btn_h_total = cta_h + 36
    btn_y1 = y_cursor + 10
    btn_y2 = btn_y1 + btn_h_total

    # Button shadow
    shadow2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd2 = ImageDraw.Draw(shadow2)
    sd2.rounded_rectangle([btn_x1 + 4, btn_y1 + 4, btn_x2 + 4, btn_y2 + 4], radius=btn_h_total // 2, fill=(0, 0, 0, 60))
    shadow2 = shadow2.filter(ImageFilter.GaussianBlur(radius=8))
    canvas = Image.alpha_composite(canvas, shadow2)
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle([btn_x1, btn_y1, btn_x2, btn_y2], radius=btn_h_total // 2, fill=accent)
    brightness = (accent[0] * 299 + accent[1] * 587 + accent[2] * 114) / 1000
    btn_text_color = (20, 20, 20) if brightness > 128 else (255, 255, 255)
    cta_x = (W - cta_w) // 2
    draw.text((cta_x, btn_y1 + 18), cta, font=cta_font, fill=btn_text_color)

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()
