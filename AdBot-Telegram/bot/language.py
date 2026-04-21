"""bot/language.py — Language detection and locale mapping (v2).

Reads user's language from Telegram user profile.
Maps language codes to full language names for Gemini instructions.
"""
import logging

logger = logging.getLogger(__name__)

# ── Language code → full name (for Gemini prompt injection) ──────────────────
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "ar": "Arabic",
    "fr": "French",
    "es": "Spanish",
    "pt": "Portuguese",
    "de": "German",
    "it": "Italian",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese (Simplified)",
    "ko": "Korean",
    "tr": "Turkish",
    "fa": "Persian (Farsi)",
    "ur": "Urdu",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ne": "Nepali",
    "sw": "Swahili",
    "ha": "Hausa",
    "yo": "Yoruba",
    "am": "Amharic",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Filipino",
}


def get_language_name(code: str) -> str:
    """
    Convert a BCP 47 / ISO 639-1 language code to a full language name.

    Args:
        code: e.g. "hi", "ar", "zh-hans", "pt-br"

    Returns:
        Full language name string, e.g. "Hindi", "Arabic"
        Falls back to "English" if unknown.
    """
    if not code:
        return "English"
    # Normalize: take base code, lowercase
    base = code.lower().split("-")[0]
    return LANGUAGE_NAMES.get(base, "English")


def get_session_language(session) -> str:
    """
    Get the language code for a user session.

    Checks (in order):
    1. session.language_code (if we stored it from Telegram user)
    2. Defaults to "en"

    Returns ISO 639-1 code (e.g. "hi", "ar", "en")
    """
    lang = getattr(session, "language_code", None) or "en"
    base = lang.lower().split("-")[0]
    return base


def extract_language_from_update(update) -> str:
    """
    Extract language code from a Telegram Update object.

    Returns ISO 639-1 base code (e.g. "hi", "ar", "en")
    """
    try:
        user = update.effective_user
        if user and user.language_code:
            code = user.language_code.lower().split("-")[0]
            logger.debug(f"Detected language from Telegram: {code} → {get_language_name(code)}")
            return code
    except Exception as e:
        logger.debug(f"Could not extract language from update: {e}")
    return "en"
