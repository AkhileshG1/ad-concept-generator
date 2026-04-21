"""bot/links.py — Canva affiliate + sharing link generators."""
from urllib.parse import quote
from config import CANVA_TEMPLATES, DEFAULT_CANVA


def get_canva(business_type: str, platform: str) -> str:
    return CANVA_TEMPLATES.get((business_type, platform), DEFAULT_CANVA)

def whatsapp_link(text: str) -> str:
    return f"https://wa.me/?text={quote(text[:1000])}"

def instagram_caption(copy: dict) -> str:
    ig = copy.get("instagram", {})
    headline = ig.get("headline") or copy.get("headline","")
    body     = ig.get("body")     or copy.get("body","")
    cta      = ig.get("cta")      or copy.get("cta","")
    tags     = ig.get("hashtags") or copy.get("hashtags",[])
    tag_str  = " ".join(f"#{t.lstrip('#')}" for t in tags)
    parts = []
    if headline: parts.append(f"✨ {headline}")
    if body:     parts.append(f"\n{body}")
    if cta:      parts.append(f"\n👉 {cta}")
    if tag_str:  parts.append(f"\n.\n.\n{tag_str}")
    return "\n".join(parts)

def whatsapp_text(copy: dict) -> str:
    wa = copy.get("whatsapp", {})
    body = wa.get("body") or copy.get("body","")
    cta  = copy.get("cta","")
    return f"{body}\n\n{cta}".strip()

def google_ad_block(copy: dict) -> str:
    g = copy.get("google", {})
    if not g: return ""
    return (
        "🔍 *Google Ad:*\n"
        f"H1: `{g.get('h1','')}`\n"
        f"H2: `{g.get('h2','')}`\n"
        f"H3: `{g.get('h3','')}`\n"
        f"D1: {g.get('d1','')}\n"
        f"D2: {g.get('d2','')}"
    )

def poster_block(copy: dict) -> str:
    p = copy.get("poster", {})
    if not p: return ""
    bullets = "\n".join(f"  • {b}" for b in p.get("bullets",[]))
    return (
        f"🖼️ *Print Poster:*\n"
        f"Headline: *{p.get('headline','')}*\n"
        f"Tagline: _{p.get('tagline','')}_\n"
        f"Benefits:\n{bullets}\n"
        f"CTA: {p.get('cta','')}"
    )
