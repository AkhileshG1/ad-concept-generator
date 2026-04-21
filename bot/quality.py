"""
bot/quality.py — Lightweight image quality validator.

Checks:
  1. Minimum byte size (rejects nearly-blank responses)
  2. Valid JPEG/PNG header magic bytes
  3. Minimum dimensions via Pillow (if available)
"""

MIN_SIZE_BYTES = 20_000        # anything under 20 KB is suspicious
MIN_DIMENSION  = 256           # pixels


def is_image_acceptable(data: bytes) -> bool:
    """Return True if the image bytes pass basic quality checks."""
    if len(data) < MIN_SIZE_BYTES:
        return False

    if not _has_valid_magic(data):
        return False

    # Try dimension check (Pillow optional)
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if w < MIN_DIMENSION or h < MIN_DIMENSION:
            return False
    except Exception:
        pass     # Pillow not installed or can't open — skip dimension check

    return True


def _has_valid_magic(data: bytes) -> bool:
    """Check known image format magic bytes."""
    jpeg_magic = b"\xff\xd8\xff"
    png_magic  = b"\x89PNG"
    webp_magic = b"RIFF"

    return (
        data[:3] == jpeg_magic
        or data[:4] == png_magic
        or data[:4] == webp_magic
    )


def describe_quality_issue(copy: dict) -> str | None:
    """
    Validate ad copy fields.
    Returns a human-readable warning string if something is off, else None.
    """
    issues = []

    headline = copy.get("headline", "")
    if len(headline) > 90:
        issues.append("⚠️ Headline is quite long — consider shortening it for impact.")

    body = copy.get("body", "")
    if len(body) < 20:
        issues.append("⚠️ Body copy seems too short.")

    cta = copy.get("cta", "")
    if not cta:
        issues.append("⚠️ No call-to-action was generated.")

    if issues:
        return "\n".join(issues)
    return None
