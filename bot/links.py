"""
bot/links.py — Generate pre-filled sharing links + Canva template suggestions.

All pure Python, no external calls.
"""
from urllib.parse import quote
from config import CANVA_TEMPLATES, DEFAULT_CANVA


def get_canva_link(business_type: str, platform: str) -> str:
    key = (business_type, platform)
    return CANVA_TEMPLATES.get(key, DEFAULT_CANVA)


def get_whatsapp_share_link(text: str) -> str:
    """Create a wa.me share link with pre-filled text."""
    encoded = quote(text[:1000])    # WhatsApp link limit
    return f"https://wa.me/?text={encoded}"


def get_instagram_caption(copy: dict) -> str:
    """Format a ready-to-paste Instagram caption."""
    ig = copy.get("instagram", {})
    headline = ig.get("headline") or copy.get("headline", "")
    body     = ig.get("body")     or copy.get("body", "")
    cta      = ig.get("cta")      or copy.get("cta", "")
    hashtags = ig.get("hashtags") or copy.get("hashtags", [])

    parts = []
    if headline:
        parts.append(f"✨ {headline}")
    if body:
        parts.append(f"\n{body}")
    if cta:
        parts.append(f"\n👉 {cta}")
    if hashtags:
        tag_str = " ".join(f"#{t.lstrip('#')}" for t in hashtags)
        parts.append(f"\n.\n.\n{tag_str}")

    return "\n".join(parts)


def get_whatsapp_message(copy: dict) -> str:
    """Return WhatsApp-formatted text."""
    wa = copy.get("whatsapp", {})
    body = wa.get("body") or copy.get("body", "")
    cta  = copy.get("cta", "")
    return f"{body}\n\n{cta}".strip()


def format_google_ad(copy: dict) -> str:
    """Format Google Ad copy for display."""
    g = copy.get("google", {})
    if not g:
        return ""
    lines = [
        "🔍 *Google Ad:*",
        f"H1: `{g.get('h1','')}`",
        f"H2: `{g.get('h2','')}`",
        f"H3: `{g.get('h3','')}`",
        f"D1: {g.get('d1','')}",
        f"D2: {g.get('d2','')}",
    ]
    return "\n".join(lines)


def format_poster_copy(copy: dict) -> str:
    """Format print poster copy for display."""
    p = copy.get("poster", {})
    if not p:
        return ""
    bullets = "\n".join(f"  • {b}" for b in p.get("bullets", []))
    return (
        f"🖼️ *Print Poster:*\n"
        f"Headline: *{p.get('headline','')}*\n"
        f"Tagline: _{p.get('tagline','')}_\n"
        f"Benefits:\n{bullets}\n"
        f"CTA: {p.get('cta','')}"
    )
