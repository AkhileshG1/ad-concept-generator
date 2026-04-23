"""bot/templates/_effects.py — Premium visual effects library for ad templates.

Agency-grade effects:
  - Auto-brightness & contrast for dark/dull product photos
  - Multi-layer drop shadows with perspective
  - Luminous glow / halo behind products
  - Frosted glass panels for text readability
  - Gradient generators (linear, radial, diagonal, mesh)
  - Noise texture overlay for premium feel
  - Scanlines for tech/dark aesthetic
  - Premium badge renderer
  - Text shadow with configurable blur
"""
import io
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageStat
from typing import Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT IMAGE ENHANCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def enhance_product(product: Image.Image, target_brightness: float = 1.35) -> Image.Image:
    """
    Auto-enhance a product photo for ad readability.
    - Boosts brightness if too dark
    - Boosts contrast & saturation
    - Sharpens edges for clarity
    """
    if product.mode != "RGBA":
        product = product.convert("RGBA")

    r, g, b, a = product.split()
    rgb = Image.merge("RGB", (r, g, b))

    stat = ImageStat.Stat(rgb)
    avg_brightness = sum(stat.mean) / 3.0

    if avg_brightness < 80:
        factor = min(target_brightness + 0.5, 2.2)
        rgb = ImageEnhance.Brightness(rgb).enhance(factor)
    elif avg_brightness < 130:
        rgb = ImageEnhance.Brightness(rgb).enhance(target_brightness)
    elif avg_brightness < 180:
        rgb = ImageEnhance.Brightness(rgb).enhance(1.1)

    # Boost contrast
    rgb = ImageEnhance.Contrast(rgb).enhance(1.2)
    # Boost saturation (more vibrant colours)
    rgb = ImageEnhance.Color(rgb).enhance(1.25)
    # Sharpen
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.4)

    enhanced = rgb.convert("RGBA")
    enhanced.putalpha(a)
    return enhanced


# ═══════════════════════════════════════════════════════════════════════════════
# SHADOW & GLOW EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

def add_drop_shadow(
    canvas: Image.Image,
    product: Image.Image,
    pos: Tuple[int, int],
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    shadow_opacity: int = 130,
    shadow_offset: Tuple[int, int] = (0, 22),
    blur_radius: int = 35,
) -> Image.Image:
    """
    Paste product onto canvas with a professional multi-layer soft drop shadow.
    """
    canvas = canvas.convert("RGBA")
    W, H = canvas.size

    # Outer soft shadow
    shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow_img = Image.new("RGBA", product.size, shadow_color + (shadow_opacity,))
    if product.mode == "RGBA":
        shadow_img.putalpha(product.getchannel("A"))
    shadow_layer.paste(
        shadow_img,
        (pos[0] + shadow_offset[0], pos[1] + shadow_offset[1]),
        shadow_img,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    # Inner tighter shadow for depth
    inner_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    inner_img = Image.new("RGBA", product.size, shadow_color + (int(shadow_opacity * 0.5),))
    if product.mode == "RGBA":
        inner_img.putalpha(product.getchannel("A"))
    inner_layer.paste(
        inner_img,
        (pos[0] + shadow_offset[0] // 2, pos[1] + shadow_offset[1] // 2),
        inner_img,
    )
    inner_layer = inner_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius // 3))
    canvas = Image.alpha_composite(canvas, inner_layer)

    # Paste product
    canvas.paste(product, pos, product if product.mode == "RGBA" else None)
    return canvas


def add_glow_behind(
    canvas: Image.Image,
    product: Image.Image,
    pos: Tuple[int, int],
    glow_color: Tuple[int, int, int] = (255, 255, 255),
    glow_opacity: int = 55,
    glow_radius: int = 70,
    glow_scale: float = 1.35,
) -> Image.Image:
    """
    Add a multi-layer luminous glow halo behind the product.
    Creates a premium "spotlight" effect used in high-end ads.
    """
    canvas = canvas.convert("RGBA")
    pw, ph = product.size
    W, H = canvas.size

    # Layer 1 — wide soft glow
    gw1 = int(pw * glow_scale * 1.3)
    gh1 = int(ph * glow_scale * 1.3)
    glow1 = Image.new("RGBA", (gw1, gh1), glow_color + (max(10, glow_opacity // 3),))
    if product.mode == "RGBA":
        a1 = product.getchannel("A").resize((gw1, gh1), Image.LANCZOS)
        glow1.putalpha(a1)
    gx1 = pos[0] - (gw1 - pw) // 2
    gy1 = pos[1] - (gh1 - ph) // 2
    gl1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gl1.paste(glow1, (gx1, gy1), glow1)
    gl1 = gl1.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    canvas = Image.alpha_composite(canvas, gl1)

    # Layer 2 — tight bright halo
    gw2 = int(pw * glow_scale)
    gh2 = int(ph * glow_scale)
    glow2 = Image.new("RGBA", (gw2, gh2), glow_color + (glow_opacity,))
    if product.mode == "RGBA":
        a2 = product.getchannel("A").resize((gw2, gh2), Image.LANCZOS)
        glow2.putalpha(a2)
    gx2 = pos[0] - (gw2 - pw) // 2
    gy2 = pos[1] - (gh2 - ph) // 2
    gl2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gl2.paste(glow2, (gx2, gy2), glow2)
    gl2 = gl2.filter(ImageFilter.GaussianBlur(radius=glow_radius // 2))
    canvas = Image.alpha_composite(canvas, gl2)

    return canvas


def add_product_reflection(
    canvas: Image.Image,
    product: Image.Image,
    pos: Tuple[int, int],
    opacity: int = 35,
    height_fraction: float = 0.25,
) -> Image.Image:
    """Add a floor reflection below the product for a studio/premium look."""
    canvas = canvas.convert("RGBA")
    W, H = canvas.size
    pw, ph = product.size

    refl_h = int(ph * height_fraction)
    if refl_h < 4:
        return canvas

    # Crop bottom portion of product, flip it
    crop = product.crop((0, ph - refl_h, pw, ph)).transpose(Image.FLIP_TOP_BOTTOM)

    # Fade using gradient mask
    mask = Image.new("L", (pw, refl_h))
    for y in range(refl_h):
        t = y / refl_h
        alpha = int(opacity * (1 - t))
        ImageDraw.Draw(mask).line([(0, y), (pw, y)], fill=alpha)

    refl = crop.convert("RGBA")
    refl.putalpha(mask)

    refl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rx = pos[0]
    ry = pos[1] + ph + 2
    if ry + refl_h <= H:
        refl_layer.paste(refl, (rx, ry), refl)
        refl_layer = refl_layer.filter(ImageFilter.GaussianBlur(radius=3))
        canvas = Image.alpha_composite(canvas, refl_layer)

    return canvas


# ═══════════════════════════════════════════════════════════════════════════════
# GRADIENT GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def make_gradient(
    size: Tuple[int, int],
    top_color: Tuple[int, int, int],
    bottom_color: Tuple[int, int, int],
    angle: float = 0.0,
) -> Image.Image:
    """
    Create a smooth vertical gradient background with smoothstep easing.
    """
    w, h = size
    base = Image.new("RGB", size)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        t = y / h
        t = t * t * (3 - 2 * t)  # smoothstep easing
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return base


def make_diagonal_gradient(
    size: Tuple[int, int],
    color_tl: Tuple[int, int, int],
    color_br: Tuple[int, int, int],
) -> Image.Image:
    """Diagonal (top-left → bottom-right) gradient for more dynamic feel."""
    w, h = size
    base = Image.new("RGB", size)
    draw = ImageDraw.Draw(base)
    for y in range(h):
        for x in range(w):
            t = (x / w + y / h) / 2
            t = t * t * (3 - 2 * t)
            r = int(color_tl[0] * (1 - t) + color_br[0] * t)
            g = int(color_tl[1] * (1 - t) + color_br[1] * t)
            b = int(color_tl[2] * (1 - t) + color_br[2] * t)
            draw.point((x, y), fill=(r, g, b))
    return base


def make_radial_glow(
    size: Tuple[int, int],
    center: Tuple[int, int],
    color: Tuple[int, int, int],
    radius: int,
    opacity: int = 80,
) -> Image.Image:
    """Create a soft radial glow overlay."""
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    for r in range(radius, 0, -3):
        t = r / radius
        alpha = int(opacity * (1 - t * t))
        draw.ellipse(
            [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
            fill=color + (alpha,),
        )
    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius // 4))
    return glow


# ═══════════════════════════════════════════════════════════════════════════════
# TEXTURE OVERLAYS
# ═══════════════════════════════════════════════════════════════════════════════

def add_noise_texture(canvas: Image.Image, intensity: int = 8) -> Image.Image:
    """Add subtle grain/noise for premium print-quality feel."""
    canvas = canvas.convert("RGBA")
    W, H = canvas.size
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pixels = noise.load()
    rng = random.Random(42)
    for y in range(H):
        for x in range(W):
            v = rng.randint(-intensity, intensity)
            pixels[x, y] = (max(0, v), max(0, v), max(0, v), abs(v) * 2)
    return Image.alpha_composite(canvas, noise)


def add_dot_pattern(
    canvas: Image.Image,
    spacing: int = 40,
    dot_size: int = 2,
    opacity: int = 14,
) -> Image.Image:
    """Subtle dot grid pattern for texture."""
    canvas = canvas.convert("RGBA")
    pattern = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(pattern)
    W, H = canvas.size
    for y in range(0, H, spacing):
        for x in range(0, W, spacing):
            p_draw.ellipse([x, y, x + dot_size, y + dot_size], fill=(255, 255, 255, opacity))
    return Image.alpha_composite(canvas, pattern)


def add_scanlines(canvas: Image.Image, gap: int = 4, opacity: int = 10) -> Image.Image:
    """Horizontal scanlines for tech/dark aesthetic."""
    canvas = canvas.convert("RGBA")
    W, H = canvas.size
    lines = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    l_draw = ImageDraw.Draw(lines)
    for y in range(0, H, gap):
        l_draw.line([(0, y), (W, y)], fill=(0, 0, 0, opacity))
    return Image.alpha_composite(canvas, lines)


def add_vignette(canvas: Image.Image, strength: int = 60) -> Image.Image:
    """Dark vignette around edges to focus attention on centre."""
    canvas = canvas.convert("RGBA")
    W, H = canvas.size
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vig)
    cx, cy = W // 2, H // 2
    steps = 40
    for i in range(steps):
        t = i / steps
        alpha = int(strength * t * t)
        margin_x = int(cx * t)
        margin_y = int(cy * t)
        draw.rectangle(
            [margin_x, margin_y, W - margin_x, H - margin_y],
            outline=(0, 0, 0, alpha),
        )
    vig = vig.filter(ImageFilter.GaussianBlur(radius=W // 6))
    return Image.alpha_composite(canvas, vig)


# ═══════════════════════════════════════════════════════════════════════════════
# FROSTED GLASS PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def add_frosted_glass_panel(
    canvas: Image.Image,
    rect: Tuple[int, int, int, int],
    color: Tuple[int, int, int] = (255, 255, 255),
    opacity: int = 18,
    radius: int = 20,
    border_opacity: int = 40,
) -> Image.Image:
    """
    Draw a frosted-glass style panel over the canvas for text readability.
    rect = (x1, y1, x2, y2)
    """
    canvas = canvas.convert("RGBA")
    x1, y1, x2, y2 = rect
    W, H = canvas.size

    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_draw = ImageDraw.Draw(panel)

    # Fill
    p_draw.rounded_rectangle(rect, radius=radius, fill=color + (opacity,))
    # Border highlight
    p_draw.rounded_rectangle(rect, radius=radius, outline=color + (border_opacity,), width=1)

    return Image.alpha_composite(canvas, panel)


# ═══════════════════════════════════════════════════════════════════════════════
# PREMIUM BADGE
# ═══════════════════════════════════════════════════════════════════════════════

def draw_premium_badge(
    draw: ImageDraw.Draw,
    canvas: Image.Image,
    text: str,
    pos: Tuple[int, int],
    font,
    bg_color: Tuple[int, int, int] = (255, 200, 50),
    text_color: Tuple[int, int, int] = (20, 20, 20),
    padding: Tuple[int, int] = (18, 8),
) -> None:
    """Draw a pill-shaped badge (e.g. 'NEW', '50% OFF', 'PRO')."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    px, py = padding
    x, y = pos
    r = (th + py * 2) // 2

    badge_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(badge_layer)
    b_draw.rounded_rectangle(
        [x, y, x + tw + px * 2, y + th + py * 2],
        radius=r, fill=bg_color + (230,),
    )
    canvas_with_badge = Image.alpha_composite(canvas, badge_layer)

    # Draw the badge back onto main canvas
    canvas.paste(canvas_with_badge)
    draw.text((x + px, y + py), text, font=font, fill=text_color)


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_text_with_shadow(
    canvas: Image.Image,
    pos: Tuple[int, int],
    text: str,
    font,
    fill: Tuple[int, int, int] = (255, 255, 255),
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    shadow_offset: int = 3,
    shadow_blur: int = 8,
    align: str = "left",
    multiline: bool = False,
) -> Image.Image:
    """Draw text (single or multiline) with a soft shadow layer."""
    canvas = canvas.convert("RGBA")
    x, y = pos

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    fn = s_draw.multiline_text if multiline else s_draw.text
    fn(
        (x + shadow_offset, y + shadow_offset),
        text, font=font,
        fill=shadow_color + (180,),
        align=align,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas = Image.alpha_composite(canvas, shadow_layer)

    draw = ImageDraw.Draw(canvas)
    fn2 = draw.multiline_text if multiline else draw.text
    fn2(pos, text, font=font, fill=fill, align=align)
    return canvas


def wrap_text(draw: ImageDraw.Draw, text: str, font, max_width: int) -> str:
    """Word-wrap text to fit within max_width pixels."""
    if not text:
        return ""
    words = text.split()
    lines = []
    current = []
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


def measure_text(draw: ImageDraw.Draw, text: str, font) -> Tuple[int, int]:
    """Return (width, height) of text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]
