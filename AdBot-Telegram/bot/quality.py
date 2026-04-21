"""bot/quality.py — Image + copy quality validator."""
from typing import Optional

MIN_BYTES = 20_000

def is_image_ok(data: bytes) -> bool:
    if not data or len(data) < MIN_BYTES:
        return False
    return data[:3] == b"\xff\xd8\xff" or data[:4] in (b"\x89PNG", b"RIFF")

def copy_warnings(copy: dict) -> Optional[str]:
    issues = []
    if len(copy.get("headline","")) > 90:
        issues.append("⚠️ Headline is long — consider shortening for impact.")
    if len(copy.get("body","")) < 20:
        issues.append("⚠️ Body copy is very short.")
    if not copy.get("cta"):
        issues.append("⚠️ No call-to-action generated.")
    return "\n".join(issues) if issues else None
