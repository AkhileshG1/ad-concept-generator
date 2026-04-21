"""bot/templates/_utils.py — Shared utilities for all ad templates.

Provides safe copy field getters that handle None, missing keys,
and edge-case content gracefully.
"""
from typing import Any, List


def safe_get(copy: dict, key: str, default: str = "") -> str:
    """
    Safely get a string field from copy dict.
    Handles: missing key, None value, non-string types.
    """
    if not copy:
        return default
    val = copy.get(key, default)
    if val is None:
        return default
    return str(val).strip() or default


def safe_bullets(copy: dict, max_items: int = 3) -> List[str]:
    """
    Safely extract bullet points from copy.poster.bullets or parse from body.
    Always returns a list (may be empty).
    """
    poster = copy.get("poster") if copy else None
    if poster and isinstance(poster, dict):
        bullets = poster.get("bullets")
        if bullets and isinstance(bullets, list):
            return [str(b) for b in bullets[:max_items] if b]

    # Fallback: extract sentences from body
    body = safe_get(copy, "body")
    if body:
        sentences = [s.strip() for s in body.replace(".", ". ").split(". ") if len(s.strip()) > 8]
        return sentences[:max_items]

    return []


def safe_brand_color(copy: dict, fallback: tuple) -> tuple:
    """
    Safely extract the first brand color from copy.brand_colors.
    Falls back to provided fallback tuple.
    """
    try:
        colors = copy.get("brand_colors") if copy else None
        if colors and isinstance(colors, list) and colors[0]:
            h = str(colors[0]).lstrip("#")
            if len(h) == 6:
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        pass
    return fallback
