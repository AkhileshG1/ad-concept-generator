"""
config.py — Centralised configuration for AdBot (Telegram Ad Generator)
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.5-flash"          # Advanced multimodal model with active quota

# ── Image: Pollinations.ai (globally available, no API key, ~5s) ──────────────
# Open access worldwide — no geo-blocks, community-driven, EU-hosted
# model=flux → FLUX is the best quality model on Pollinations (follows prompts much better than default SDXL)
# negative  → negative prompt support (blocks watermarks, text, bad anatomy etc.)
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}"
POLLINATIONS_PARAMS = "model=flux&width=1024&height=1024&nologo=true&enhance=true&seed={seed}&negative={negative}"

# Fallback: HuggingFace SDXL-Turbo
HF_API_KEY   = os.getenv("HF_API_KEY", "")
HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"

# ── Canva Affiliate Tag (passive income) ──────────────────────────────────────
# Sign up free at https://www.canva.com/affiliates/ → get your affiliate tag
# Replace "YOUR_AFFILIATE_TAG" with your tag to earn 25–80% commission
CANVA_AFFILIATE_TAG = os.getenv("CANVA_AFFILIATE_TAG", "")

def canva_url(query: str) -> str:
    base = f"https://www.canva.com/templates/?query={query}"
    if CANVA_AFFILIATE_TAG:
        return f"{base}&referrer={CANVA_AFFILIATE_TAG}"
    return base

# ── Canva Templates per industry + platform ───────────────────────────────────
CANVA_TEMPLATES = {
    ("food",     "instagram"): canva_url("food+instagram+post"),
    ("food",     "poster"):    canva_url("restaurant+menu+poster"),
    ("food",     "whatsapp"):  canva_url("food+sale+flyer"),
    ("fashion",  "instagram"): canva_url("fashion+instagram+post"),
    ("fashion",  "poster"):    canva_url("fashion+sale+poster"),
    ("fashion",  "whatsapp"):  canva_url("clothing+flyer"),
    ("tech",     "instagram"): canva_url("tech+product+instagram"),
    ("tech",     "poster"):    canva_url("technology+poster"),
    ("tech",     "whatsapp"):  canva_url("tech+promotion+flyer"),
    ("services", "instagram"): canva_url("service+business+instagram"),
    ("services", "poster"):    canva_url("professional+service+poster"),
    ("services", "whatsapp"):  canva_url("business+service+flyer"),
}
DEFAULT_CANVA = canva_url("ad+poster")

# ── Monetisation: Freemium Tiers ──────────────────────────────────────────────
#
#  FREE  → 3 ads/day, 2 images/day, single platform only
#  PRO   → unlimited ads, 10 images/day, all platforms, priority support
#
# Telegram Stars pricing (1 Star ≈ $0.013 USD)
# 50 Stars = ~$0.65  → 1 week PRO
# 150 Stars = ~$1.95 → 1 month PRO
# 500 Stars = ~$6.50 → 3 months PRO  ← best value upsell
#
FREE_ADS_PER_DAY    = 3
FREE_IMAGES_PER_DAY = 2
PRO_ADS_PER_DAY     = 999    # effectively unlimited
PRO_IMAGES_PER_DAY  = 10

STARS_WEEKLY  = 50
STARS_MONTHLY = 150
STARS_QUARTERLY = 500

# ── Session TTL ───────────────────────────────────────────────────────────────
SESSION_TTL_SECONDS = 3600     # 1 hour inactivity clears session

# ── States ────────────────────────────────────────────────────────────────────
class State:
    IDLE            = "idle"
    CHOOSE_BUSINESS = "choose_business"
    CHOOSE_PLATFORM = "choose_platform"
    GET_PRODUCT     = "get_product"
    GET_USP         = "get_usp"
    GET_AUDIENCE    = "get_audience"
    WAITING_PHOTO   = "waiting_photo"
    GENERATING_COPY = "generating_copy"
    AWAITING_RATING = "awaiting_rating"
    GENERATING_IMG  = "generating_img"
    DONE            = "done"

# ── Business categories ───────────────────────────────────────────────────────
BUSINESS_TYPES = {
    "🍕 Food & Beverage":       "food",
    "👗 Fashion & Clothing":    "fashion",
    "💻 Tech & Electronics":    "tech",
    "🔧 Services & Consulting": "services",
    "🎯 Other":                 "other",
}

# ── Target platforms ──────────────────────────────────────────────────────────
PLATFORMS_FREE = {
    "📸 Instagram Post":       "instagram",
    "💬 WhatsApp Forward":     "whatsapp",
}
PLATFORMS_PRO = {
    "🔍 Google Ad":            "google",
    "🖼️ Print Poster":        "poster",
    "📦 Full Ad Pack (All) ⭐": "all",
}
ALL_PLATFORMS = {**PLATFORMS_FREE, **PLATFORMS_PRO}
