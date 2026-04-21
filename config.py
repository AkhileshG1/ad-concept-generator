"""
config.py — Centralised configuration for the AI Ad Bot
"""
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"          # free tier, fast

# ── Image Generation ─────────────────────────────────────────────────────────
# Primary: Pollinations.ai (no key, ~5s)
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}?width=1024&height=1024&nologo=true&seed={seed}"

# Fallback: HuggingFace SDXL-Turbo (faster than SDXL)
HF_API_KEY = os.getenv("HF_API_KEY", "")
HF_MODEL_URL = "https://api-inference.huggingface.co/models/stabilityai/sdxl-turbo"

# ── Rate Limiting ─────────────────────────────────────────────────────────────
MAX_ADS_PER_DAY = 10          # per user
MAX_IMAGES_PER_DAY = 5        # per user (heavier API call)

# ── Canva Template URLs by industry + platform ────────────────────────────────
CANVA_TEMPLATES = {
    ("food", "instagram"):  "https://www.canva.com/templates/?query=food+instagram+post",
    ("food", "poster"):     "https://www.canva.com/templates/?query=restaurant+menu+poster",
    ("food", "whatsapp"):   "https://www.canva.com/templates/?query=food+sale+flyer",
    ("fashion", "instagram"): "https://www.canva.com/templates/?query=fashion+instagram+post",
    ("fashion", "poster"):  "https://www.canva.com/templates/?query=fashion+sale+poster",
    ("fashion", "whatsapp"): "https://www.canva.com/templates/?query=clothing+flyer",
    ("tech", "instagram"):  "https://www.canva.com/templates/?query=tech+product+instagram",
    ("tech", "poster"):     "https://www.canva.com/templates/?query=technology+poster",
    ("tech", "whatsapp"):   "https://www.canva.com/templates/?query=tech+promotion+flyer",
    ("services", "instagram"): "https://www.canva.com/templates/?query=service+business+instagram",
    ("services", "poster"): "https://www.canva.com/templates/?query=professional+service+poster",
    ("services", "whatsapp"): "https://www.canva.com/templates/?query=business+service+flyer",
}
DEFAULT_CANVA = "https://www.canva.com/templates/?query=ad+poster"

# ── Session TTL ───────────────────────────────────────────────────────────────
SESSION_TTL_SECONDS = 3600     # 1 hour of inactivity clears session

# ── Conversation states ───────────────────────────────────────────────────────
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
    "🍕 Food & Beverage": "food",
    "👗 Fashion & Clothing": "fashion",
    "💻 Tech & Electronics": "tech",
    "🔧 Services & Consulting": "services",
    "🎯 Other": "other",
}

# ── Target platforms ──────────────────────────────────────────────────────────
PLATFORMS = {
    "📸 Instagram Post": "instagram",
    "💬 WhatsApp Forward": "whatsapp",
    "🔍 Google Ad": "google",
    "🖼️ Print Poster": "poster",
    "📦 Full Ad Pack (All)": "all",
}
