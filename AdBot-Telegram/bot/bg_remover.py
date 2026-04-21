"""bot/bg_remover.py — Product background removal via rembg.

Uses the U2Net model (CPU-based, no API, no cost).
First call downloads the model (~170MB). Subsequent calls are instant.

Public API:
    remove_background(photo_bytes: bytes) -> bytes   # Returns RGBA PNG
    extract_dominant_color(photo_bytes: bytes) -> tuple  # Returns (R, G, B)
"""
import io
import logging
from PIL import Image

logger = logging.getLogger(__name__)

# rembg is lazy-imported so the bot starts even if not installed yet
_rembg = None


def _get_rembg():
    """Lazy-load rembg to avoid slowing down bot startup."""
    global _rembg
    if _rembg is None:
        try:
            import rembg
            _rembg = rembg
            logger.info("rembg loaded successfully")
        except ImportError:
            logger.error("rembg not installed. Run: pip install rembg onnxruntime")
            raise
    return _rembg


def remove_background(photo_bytes: bytes, model: str = "u2net") -> bytes:
    """
    Remove the background from a product photo.

    Args:
        photo_bytes: Raw JPEG or PNG bytes (from Telegram photo download)
        model: rembg model to use. Options:
               - "u2net"            → general purpose (recommended)
               - "u2net_human_seg"  → for people/fashion
               - "isnet-general-use" → high quality, slower

    Returns:
        PNG bytes with transparent (RGBA) background.
        Falls back to original image (converted to RGBA) if rembg fails.
    """
    try:
        rembg = _get_rembg()
        logger.info(f"Removing background with model={model} ...")

        result_bytes = rembg.remove(
            photo_bytes,
            session=rembg.new_session(model),
            alpha_matting=True,
            alpha_matting_foreground_threshold=240,
            alpha_matting_background_threshold=10,
            alpha_matting_erode_size=10,
        )

        # Validate output
        img = Image.open(io.BytesIO(result_bytes))
        if img.mode != "RGBA":
            img = img.convert("RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            result_bytes = buf.getvalue()

        logger.info(f"Background removed. Output size: {len(result_bytes):,} bytes, mode: {img.mode}")
        return result_bytes

    except Exception as e:
        logger.warning(f"Background removal failed ({e}). Using original image.")
        return _convert_to_rgba_png(photo_bytes)


def remove_background_simple(photo_bytes: bytes) -> bytes:
    """
    Faster background removal without alpha matting.
    Use when speed matters more than edge quality.
    """
    try:
        rembg = _get_rembg()
        result_bytes = rembg.remove(photo_bytes)
        return result_bytes
    except Exception as e:
        logger.warning(f"Simple background removal failed ({e}). Using original.")
        return _convert_to_rgba_png(photo_bytes)


def _convert_to_rgba_png(photo_bytes: bytes) -> bytes:
    """Convert any image to RGBA PNG (fallback when rembg fails)."""
    try:
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return photo_bytes


def extract_dominant_color(photo_bytes: bytes) -> tuple:
    """
    Extract the dominant color from an image.
    Used for auto-matching brand color palette.

    Returns:
        (R, G, B) tuple of the dominant color.
        Falls back to (100, 100, 200) (neutral blue) on error.
    """
    try:
        img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        # Resize for speed — we only need rough color
        img = img.resize((50, 50), Image.LANCZOS)

        # Get all pixels
        pixels = list(img.getdata())

        # Filter out near-white and near-black (background noise)
        filtered = [
            p for p in pixels
            if not (p[0] > 230 and p[1] > 230 and p[2] > 230)  # not white
            and not (p[0] < 25 and p[1] < 25 and p[2] < 25)    # not black
        ]

        if not filtered:
            filtered = pixels

        # Average of filtered pixels = dominant color
        r = int(sum(p[0] for p in filtered) / len(filtered))
        g = int(sum(p[1] for p in filtered) / len(filtered))
        b = int(sum(p[2] for p in filtered) / len(filtered))

        return (r, g, b)

    except Exception as e:
        logger.warning(f"Could not extract dominant color: {e}")
        return (100, 130, 200)
