"""bot/font_manager.py — Multilingual Noto font manager.

Downloads Noto fonts on first run (one-time, ~10MB total).
Auto-selects correct font file based on language/script.
Handles Arabic RTL text reshaping.
"""
import os
import urllib.request
from pathlib import Path
from typing import Optional, Dict
from PIL import ImageFont
import logging

logger = logging.getLogger(__name__)

# ── Font directory (relative to project root) ─────────────────────────────────
FONTS_DIR = Path(__file__).parent.parent / "fonts"
FONTS_DIR.mkdir(exist_ok=True)

# ── Noto font URLs — Google Fonts API (fast CDN) ──────────────────────────────
# These are the direct download links from fonts.gstatic.com (Google's CDN)
FONT_URLS = {
    "latin":          "https://fonts.gstatic.com/s/notosans/v36/o-0NIpQlx3QUlC5A4PNjThZVZNyoX24.ttf",
    "latin_bold":     "https://fonts.gstatic.com/s/notosans/v36/o-0mIpQlx3QUlC5A4PNjFhZVZNyoX24.ttf",
    "devanagari":     "https://fonts.gstatic.com/s/notosansdevanagari/v26/TuGoUUFzXI5FBtUq5a8bjKYTZjtB_FNMiM3i6Hl9gQ.ttf",
    "devanagari_bold":"https://fonts.gstatic.com/s/notosansdevanagari/v26/TuGoUUFzXI5FBtUq5a8bjKYTZjtB_FNMiM3i6Hl9gQ.ttf",
    "arabic":         "https://fonts.gstatic.com/s/notosansarabic/v18/nwpxtLGrOAZMl5nJ_wfgRg3DrWFZWsnVBJ_sS6tlqHHFlhQ5l3sQWIHPqzvsalse.ttf",
    "arabic_bold":    "https://fonts.gstatic.com/s/notosansarabic/v18/nwpxtLGrOAZMl5nJ_wfgRg3DrWFZWsnVBJ_sS6tlqHHFlhQ5l3sQWIHPqzvsalse.ttf",
    "jp":             "https://fonts.gstatic.com/s/notosansjp/v52/-F62fjtqLzI2JPCgQBnanlhczCDEF_sV.ttf",
    "sc":             "https://fonts.gstatic.com/s/notosanssc/v36/k3kCo84MPvpLmixcA63oeAL7Iqp5IZJF9bmaG9_FnYxNbPzS5HE.ttf",
    "korean":         "https://fonts.gstatic.com/s/notosanskr/v36/PbyxFmXiEBPT4ITbgNA5Cgms3VYcOA-vvnIzzuoyeLTq8H4hfeE.ttf",
    "thai":           "https://fonts.gstatic.com/s/notosansthai/v20/iJWnBXeUZi_OHPqn4wq6hQ2_hbJ1xyN9wd43SofLWg.ttf",
}

# ── System fonts fallback (macOS / Linux) ─────────────────────────────────────
SYSTEM_FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/SFNSDisplay.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
]


# ── Language code → font key mapping ──────────────────────────────────────────
LANGUAGE_FONT_MAP = {
    # Arabic script
    "ar": "arabic", "fa": "arabic", "ur": "arabic", "ps": "arabic",
    # Devanagari script (Hindi, Marathi, Nepali)
    "hi": "devanagari", "mr": "devanagari", "ne": "devanagari",
    # CJK
    "ja": "jp", "zh": "sc", "zh-hans": "sc", "zh-hant": "sc",
    "ko": "korean",
    # Thai
    "th": "thai",
}

# Languages that render right-to-left
RTL_LANGUAGES = {"ar", "fa", "ur", "he", "ps", "dv"}

# Cache: font_key → {size → ImageFont}
_font_cache: Dict[str, ImageFont.FreeTypeFont] = {}
_download_attempted: set = set()


def _font_path(key: str) -> Path:
    filename = key.replace("/", "_") + ".ttf"
    return FONTS_DIR / filename


def _ensure_font_downloaded(key: str) -> bool:
    """Download font if not already present. Returns True on success."""
    path = _font_path(key)
    if path.exists():
        return True
    if key in _download_attempted:
        return False
    _download_attempted.add(key)

    url = FONT_URLS.get(key)
    if not url:
        logger.warning(f"No URL configured for font key: {key}")
        return False

    try:
        logger.info(f"Downloading font '{key}' from Google Fonts...")
        urllib.request.urlretrieve(url, path)
        logger.info(f"Font '{key}' downloaded → {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download font '{key}': {e}")
        return False


def _ensure_latin_fallback() -> bool:
    """Ensure the base Latin font is always available."""
    return _ensure_font_downloaded("latin")


def _get_system_font(size: int) -> Optional[ImageFont.FreeTypeFont]:
    """Try to load a system-installed font as fallback."""
    for path in SYSTEM_FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return None


def _ensure_font_downloaded_with_timeout(key: str, timeout: int = 8) -> bool:
    """Download font with a timeout. Returns True on success."""
    path = _font_path(key)
    if path.exists():
        return True
    if key in _download_attempted:
        return False
    _download_attempted.add(key)

    url = FONT_URLS.get(key)
    if not url:
        return False

    try:
        logger.info(f"Downloading font '{key}' from fonts.gstatic.com...")
        req = urllib.request.Request(url, headers={"User-Agent": "AdBot/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read()
        with open(path, "wb") as f:
            f.write(data)
        logger.info(f"Font '{key}' downloaded → {path} ({len(data):,} bytes)")
        return True
    except Exception as e:
        logger.warning(f"Font download failed for '{key}': {e}")
        return False


def get_font(language: str = "en", size: int = 40, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Return a Pillow ImageFont for the given language and size.

    Priority order:
    1. Cached font
    2. Downloaded Noto font (if already on disk)
    3. System font (macOS/Linux — instant, no download)
    4. Download Noto font (8s timeout)
    5. Pillow built-in default
    """
    lang = (language or "en").lower().split("-")[0]
    font_key = LANGUAGE_FONT_MAP.get(lang, "latin")
    if bold:
        bold_key = font_key + "_bold"
        if bold_key in FONT_URLS:
            font_key = bold_key

    cache_key = f"{font_key}_{size}"
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    # 1. Try already-downloaded Noto font
    noto_path = _font_path(font_key)
    if noto_path.exists():
        try:
            font = ImageFont.truetype(str(noto_path), size)
            _font_cache[cache_key] = font
            return font
        except Exception as e:
            logger.warning(f"Cached font '{font_key}' unreadable: {e}")

    # 2. System font (instant — no download needed)
    sys_font = _get_system_font(size)
    if sys_font:
        logger.debug(f"Using system font for lang={lang}, size={size}")
        _font_cache[cache_key] = sys_font
        return sys_font

    # 3. Try to download Noto (with timeout)
    if _ensure_font_downloaded_with_timeout(font_key):
        try:
            font = ImageFont.truetype(str(_font_path(font_key)), size)
            _font_cache[cache_key] = font
            return font
        except Exception as e:
            logger.warning(f"Could not load downloaded font '{font_key}': {e}")

    # 4. Try Latin fallback download
    latin_key = "latin_bold" if bold else "latin"
    if _ensure_font_downloaded_with_timeout(latin_key):
        try:
            font = ImageFont.truetype(str(_font_path(latin_key)), size)
            _font_cache[cache_key] = font
            return font
        except Exception:
            pass

    # 5. Pillow default
    logger.warning(f"Using Pillow default font (lang={lang}, size={size})")
    return ImageFont.load_default()


def is_rtl(language: str) -> bool:
    """Return True if the language reads right-to-left."""
    lang = (language or "en").lower().split("-")[0]
    return lang in RTL_LANGUAGES


def prepare_text(text: str, language: str) -> str:
    """
    Reshape and reorder text for correct rendering.
    Required for Arabic/Farsi — no-op for other languages.
    """
    lang = (language or "en").lower().split("-")[0]
    if lang not in RTL_LANGUAGES:
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except ImportError:
        logger.warning("arabic-reshaper / python-bidi not installed; Arabic may render incorrectly")
        return text


def preload_fonts(languages: list[str] = None):
    """
    Pre-download all needed fonts at startup (optional but recommended).
    Call this once during bot initialization.
    """
    keys_to_load = {"latin", "latin_bold"}
    if languages:
        for lang in languages:
            key = LANGUAGE_FONT_MAP.get(lang.lower(), "latin")
            keys_to_load.add(key)
    else:
        # Download all fonts
        keys_to_load = set(FONT_URLS.keys())

    for key in keys_to_load:
        _ensure_font_downloaded(key)
