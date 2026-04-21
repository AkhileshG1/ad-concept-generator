"""bot/templates/_effects.py — Professional visual effects for ad templates.

Provides reusable image enhancement functions that make product photos
look like they came from a professional photo studio:
  - Auto-brightness & contrast correction for dark product photos
  - Professional drop shadow with perspective
  - Glow/halo effect behind products
  - Gradient generators (linear, radial, diagonal)
  - Text shadow rendering
"""
import io
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageStat
from typing import Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT IMAGE ENHANCEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def enhance_product(product: Image.Image, target_brightness: float = 1.3) -> Image.Image:
    """
    Auto-enhance a product photo for ad readability.
    - Boosts brightness if the image is too dark
    - Increases contrast slightly for pop
    - Sharpens edges for clarity
    """
    if product.mode != "RGBA":
        product = product.convert("RGBA")

    # Split into RGB + Alpha
    r, g, b, a = product.split()
    rgb = Image.merge("RGB", (r, g, b))

    # Measure average brightness
    stat = ImageStat.Stat(rgb)
    avg_brightness = sum(stat.mean) / 3.0  # 0-255

    # If product is dark (< 100 avg brightness), boost it
    if avg_brightness < 100:
        factor = min(target_brightness + 0.3, 2.0)
        rgb = ImageEnhance.Brightness(rgb).enhance(factor)
    elif avg_brightness < 150:
        rgb = ImageEnhance.Brightness(rgb).enhance(target_brightness)

    # Boost contrast slightly
    rgb = ImageEnhance.Contrast(rgb).enhance(1.15)

    # Sharpen
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.2)

    # Recombine with original alpha
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
    shadow_opacity: int = 100,
    shadow_offset: Tuple[int, int] = (0, 20),
    blur_radius: int = 30,
) -> Image.Image:
    """
    Paste product onto canvas with a professional soft drop shadow.
    Much more realistic than a simple offset shadow.
    """
    canvas = canvas.convert("RGBA")

    # Create shadow layer
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
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

    # Paste product
    canvas.paste(product, pos, product if product.mode == "RGBA" else None)
    return canvas


def add_glow_behind(
    canvas: Image.Image,
    product: Image.Image,
    pos: Tuple[int, int],
    glow_color: Tuple[int, int, int] = (255, 255, 255),
    glow_opacity: int = 50,
    glow_radius: int = 60,
    glow_scale: float = 1.3,
) -> Image.Image:
    """
    Add a soft luminous glow behind the product — makes it pop off the background.
    Used in premium ads to give products a "hero" feel.
    """
    canvas = canvas.convert("RGBA")
    pw, ph = product.size

    # Create overscaled glow
    glow_w = int(pw * glow_scale)
    glow_h = int(ph * glow_scale)
    glow_img = Image.new("RGBA", (glow_w, glow_h), glow_color + (glow_opacity,))

    if product.mode == "RGBA":
        # Scale alpha channel to glow size
        alpha = product.getchannel("A").resize((glow_w, glow_h), Image.LANCZOS)
        glow_img.putalpha(alpha)

    # Center glow behind product
    glow_x = pos[0] - (glow_w - pw) // 2
    glow_y = pos[1] - (glow_h - ph) // 2

    glow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow_layer.paste(glow_img, (glow_x, glow_y), glow_img)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))

    canvas = Image.alpha_composite(canvas, glow_layer)
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
    Create a smooth vertical gradient background.
    angle=0 is purely vertical; angle!=0 adds a slight diagonal feel.
    """
    w, h = size
    base = Image.new("RGB", size)
    draw = ImageDraw.Draw(base)

    for y in range(h):
        t = y / h
        # Apply easing for smoother gradients
        t = t * t * (3 - 2 * t)  # smoothstep
        r = int(top_color[0] * (1 - t) + bottom_color[0] * t)
        g = int(top_color[1] * (1 - t) + bottom_color[1] * t)
        b = int(top_color[2] * (1 - t) + bottom_color[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

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

    # Draw concentric circles with decreasing opacity
    for r in range(radius, 0, -2):
        t = r / radius
        alpha = int(opacity * (1 - t * t))  # quadratic falloff
        draw.ellipse(
            [center[0] - r, center[1] - r, center[0] + r, center[1] + r],
            fill=color + (alpha,),
        )

    glow = glow.filter(ImageFilter.GaussianBlur(radius=radius // 3))
    return glow


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT EFFECTS
# ═══════════════════════════════════════════════════════════════════════════════

def draw_text_with_shadow(
    draw: ImageDraw.Draw,
    canvas: Image.Image,
    pos: Tuple[int, int],
    text: str,
    font,
    fill: Tuple[int, int, int] = (255, 255, 255),
    shadow_color: Tuple[int, int, int] = (0, 0, 0),
    shadow_offset: int = 3,
    shadow_blur: int = 6,
    align: str = "left",
) -> None:
    """Draw text with a soft shadow for readability on any background."""
    x, y = pos

    # Create shadow on separate layer
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    s_draw.text(
        (x + shadow_offset, y + shadow_offset),
        text, font=font,
        fill=shadow_color + (160,),
        align=align,
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=shadow_blur))

    # Composite shadow then text
    composite = Image.alpha_composite(canvas.convert("RGBA"), shadow_layer)
    c_draw = ImageDraw.Draw(composite)
    c_draw.text(pos, text, font=font, fill=fill, align=align)

    # Copy back to canvas
    canvas.paste(composite)
    return composite


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
