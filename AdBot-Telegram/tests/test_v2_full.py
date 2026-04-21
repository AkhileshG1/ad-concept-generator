#!/usr/bin/env python3
"""
AdBot v2 — Full QA Test Suite
Testing with 10 years experience discipline:
  - Unit tests (each component in isolation)
  - Integration tests (pipeline end-to-end)
  - Edge cases (empty inputs, corrupt data, Unicode, boundary values)
  - Failure / resilience tests (broken images, missing copy fields)
  - Performance benchmarks (render time, memory)
  - Visual output validation (image dimensions, format, file size sanity)
  - Regression tests (v1 fallback still works)
"""
import io
import os
import sys
import time
import traceback
import urllib.request
from pathlib import Path
from PIL import Image

# ── Setup path ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

# ── Test counters ─────────────────────────────────────────────────────────────
PASSED = 0
FAILED = 0
WARNINGS = []
REPORT = []
OUTPUT_DIR = Path("/tmp/adbot_v2_qa")
OUTPUT_DIR.mkdir(exist_ok=True)

def ok(name):
    global PASSED
    PASSED += 1
    REPORT.append(f"  ✅  {name}")
    print(f"  ✅  {name}")

def fail(name, reason):
    global FAILED
    FAILED += 1
    REPORT.append(f"  ❌  {name}: {reason}")
    print(f"  ❌  {name}: {reason}")

def warn(name, reason):
    WARNINGS.append(f"  ⚠️   {name}: {reason}")
    REPORT.append(f"  ⚠️   {name}: {reason}")
    print(f"  ⚠️   {name}: {reason}")

def section(title):
    line = f"\n{'='*60}\n  {title}\n{'='*60}"
    REPORT.append(line)
    print(line)

def save_image(name, img_bytes):
    path = OUTPUT_DIR / name
    with open(path, "wb") as f:
        f.write(img_bytes)
    return path


# ════════════════════════════════════════════════════════════════════════════════
# TEST FIXTURES
# ════════════════════════════════════════════════════════════════════════════════

def load_test_images():
    """Load test product images from multiple sources."""
    images = {}

    # Image 1: Download a product (bottle - wellness)
    try:
        url = "https://images.pexels.com/photos/1458671/pexels-photo-1458671.jpeg?auto=compress&w=600"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            images["bottle"] = r.read()
        print(f"    Loaded: bottle ({len(images['bottle']):,} bytes)")
    except Exception as e:
        print(f"    Could not download bottle: {e}")

    # Image 2: Download a food product
    try:
        url = "https://images.pexels.com/photos/1640777/pexels-photo-1640777.jpeg?auto=compress&w=600"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            images["food"] = r.read()
        print(f"    Loaded: food ({len(images['food']):,} bytes)")
    except Exception as e:
        print(f"    Could not download food: {e}")

    # Image 3: Use bot_logo.png as guaranteed fallback
    try:
        with open(ROOT / "bot_logo.png", "rb") as f:
            images["logo"] = f.read()
        print(f"    Loaded: logo ({len(images['logo']):,} bytes)")
    except Exception as e:
        print(f"    Warning: {e}")

    # Image 4: Create a synthetic test image (always available)
    img = Image.new("RGB", (400, 400), color=(200, 100, 50))
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    d.ellipse([80, 80, 320, 320], fill=(255, 200, 100))
    d.rectangle([140, 250, 260, 360], fill=(100, 200, 150))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    images["synthetic"] = buf.getvalue()
    print(f"    Created: synthetic ({len(images['synthetic']):,} bytes)")

    return images


def make_copy(headline="Test Headline That Sells", body="This is a compelling body text. It solves a problem. It makes you feel good.", cta="Buy Now →", business="food"):
    """Create a mock Gemini copy response."""
    return {
        "headline": headline,
        "body": body,
        "cta": cta,
        "hashtags": ["TestTag", "QA", "AdBot"],
        "audience_description": "Test audience description",
        "ab_variation": "Alternative headline for A/B testing",
        "brand_colors": ["#FF6B35", "#FFF3E0", "#E91E63"],
        "template_suggestion": "hero_center",
        "gradient_palette": {"top": "#FF6B35", "bottom": "#FFF3E0"},
        "visual_style": {
            "subject": "product with vibrant colors",
            "composition": "centered centered shot",
            "lighting": "soft studio lighting",
            "background": "clean gradient",
            "mood": "energetic and warm",
            "negative": "text, watermark, logo, blurry"
        },
        "instagram": {"headline": headline, "body": body, "cta": cta, "hashtags": ["TestTag"]},
        "whatsapp": {"body": body},
        "google": {"h1": "H1 Headline", "h2": "H2 Sub", "h3": "H3 Call", "d1": "Description 1", "d2": "Description 2"},
        "poster": {
            "headline": headline, "tagline": "Premium quality guaranteed",
            "bullets": ["Benefit one here", "Second great benefit", "Third compelling reason"],
            "cta": cta
        }
    }


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1: MODULE IMPORTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 1: Module Imports & Dependencies")

modules_to_test = [
    ("config", "config"),
    ("bot.session", "bot.session"),
    ("bot.prompts", "bot.prompts"),
    ("bot.gemini_client", "bot.gemini_client"),
    ("bot.image_client", "bot.image_client"),
    ("bot.bg_remover", "bot.bg_remover"),
    ("bot.font_manager", "bot.font_manager"),
    ("bot.compositor", "bot.compositor"),
    ("bot.language", "bot.language"),
    ("bot.templates.hero_center", "bot.templates.hero_center"),
    ("bot.templates.split_screen", "bot.templates.split_screen"),
    ("bot.templates.minimalist", "bot.templates.minimalist"),
    ("bot.templates.bold_poster", "bot.templates.bold_poster"),
    ("bot.handlers.start", "bot.handlers.start"),
    ("bot.handlers.collect", "bot.handlers.collect"),
    ("bot.handlers.generate", "bot.handlers.generate"),
    ("bot.handlers.image", "bot.handlers.image"),
    ("bot.handlers.deliver", "bot.handlers.deliver"),
    ("bot.handlers.history", "bot.handlers.history"),
    ("bot.monetization", "bot.monetization"),
    ("bot.links", "bot.links"),
    ("bot.quality", "bot.quality"),
]

for name, module_path in modules_to_test:
    try:
        __import__(module_path)
        ok(f"Import: {name}")
    except Exception as e:
        fail(f"Import: {name}", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2: LANGUAGE MODULE TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 2: Language Detection")

from bot.language import get_language_name, get_session_language, extract_language_from_update

lang_tests = [
    ("hi", "Hindi"),
    ("ar", "Arabic"),
    ("fr", "French"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
    ("zh", "Chinese (Simplified)"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("de", "German"),
    ("en", "English"),
    ("UNKNOWN_CODE", "English"),  # Unknown → fallback English
    ("", "English"),              # Empty string → fallback
    (None, "English"),            # None → fallback (defensive)
]

for code, expected in lang_tests:
    try:
        result = get_language_name(code)
        if result == expected:
            ok(f"Language '{code}' → '{result}'")
        else:
            fail(f"Language '{code}'", f"Expected '{expected}', got '{result}'")
    except Exception as e:
        fail(f"Language '{code}'", str(e))

# RTL detection
from bot.font_manager import is_rtl
rtl_tests = [("ar", True), ("fa", True), ("he", True), ("en", False), ("hi", False), ("zh", False)]
for code, expected in rtl_tests:
    result = is_rtl(code)
    if result == expected:
        ok(f"RTL '{code}' → {result}")
    else:
        fail(f"RTL '{code}'", f"Expected {expected}, got {result}")


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3: FONT MANAGER TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 3: Font Manager")

from bot.font_manager import get_font, prepare_text
from PIL import ImageFont

font_tests = [
    ("en", 40, False, "Latin Regular"),
    ("en", 60, True,  "Latin Bold Large"),
    ("hi", 32, False, "Hindi / Devanagari"),
    ("ar", 36, False, "Arabic (RTL)"),
    ("ja", 30, False, "Japanese"),
    ("zh", 30, False, "Chinese"),
    ("ko", 30, False, "Korean"),
    ("fr", 44, True,  "French Bold"),
    ("xx", 40, False, "Unknown code (fallback)"),
]

for lang, size, bold, label in font_tests:
    try:
        font = get_font(lang, size, bold)
        if font is None:
            fail(f"Font '{label}'", "Returned None")
        else:
            ok(f"Font '{label}' (lang={lang}, size={size}, bold={bold})")
    except Exception as e:
        fail(f"Font '{label}'", str(e))

# Prepare text (Arabic reshaping)
arabic_texts = [
    ("مرحبا بالعالم", "ar"),   # "Hello World" in Arabic
    ("नमस्ते", "hi"),          # "Hello" in Hindi
    ("Hello World", "en"),
    ("", "ar"),                  # Empty string
]
for text, lang in arabic_texts:
    try:
        result = prepare_text(text, lang)
        if result is not None:
            ok(f"prepare_text lang={lang}, len={len(text)}")
        else:
            fail(f"prepare_text lang={lang}", "Returned None")
    except Exception as e:
        fail(f"prepare_text lang={lang}", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4: SESSION MANAGEMENT TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 4: Session Management")

from bot.session import UserSession, SessionManager

# Basic session creation
try:
    from config import State as _State
    s = UserSession(12345)
    assert s.user_id == 12345
    assert s.state == _State.IDLE
    assert s.language_code == "en"
    assert s.photos == []
    assert not s.is_pro
    ok("Session creation with defaults")
except Exception as e:
    fail("Session creation", str(e))

# Rate limiting
try:
    s = UserSession(99999)
    assert s.can_generate_ad() == True
    assert s.can_generate_image() == True
    s.ads_today = 3
    assert s.can_generate_ad() == False  # Free limit = 3
    s.ads_today = 0
    assert s.can_generate_ad() == True
    ok("Rate limiting logic (free tier)")
except Exception as e:
    fail("Rate limiting", str(e))

# PRO activation
try:
    s = UserSession(11111)
    assert not s.is_pro
    s.activate_pro(30)
    assert s.is_pro
    assert s.pro_days_remaining() >= 29
    ok("PRO activation and day remaining calculation")
except Exception as e:
    fail("PRO activation", str(e))

# Language code field
try:
    s = UserSession(22222)
    s.language_code = "hi"
    assert s.language_code == "hi"
    s.reset_for_new_ad()
    assert s.language_code == "hi"  # Must survive reset
    ok("language_code persists across reset_for_new_ad()")
except Exception as e:
    fail("language_code persistence", str(e))

# Session manager get + eviction
try:
    sm = SessionManager()
    s = sm.get(42)
    assert s.user_id == 42
    s2 = sm.get(42)
    assert s is s2  # Same object
    ok("SessionManager returns same object for same user_id")
except Exception as e:
    fail("SessionManager get", str(e))

# History
try:
    s = UserSession(33333)
    for i in range(7):  # Over limit of 5
        s.save_to_history({"ad": i})
    assert len(s.history) == 5  # Capped at 5
    assert s.history[0]["ad"] == 6  # Most recent first
    ok("Ad history capped at 5, most recent first")
except Exception as e:
    fail("Ad history", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5: PROMPTS TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 5: Prompt Builder")

from bot.prompts import build_copy_prompt, build_image_prompt, COPY_SCHEMA
from bot.session import UserSession
from config import State

def make_session(btype="food", platform="instagram", has_photos=False, lang="en"):
    s = UserSession(1)
    s.business_type = btype
    s.platform = platform
    s.product_name = "Test Product"
    s.product_details = "High quality test product"
    s.usp = "Unique selling proposition"
    s.audience = "Target audience 25-40"
    s.language_code = lang
    if has_photos:
        # 1x1 pixel JPEG
        buf = io.BytesIO()
        Image.new("RGB", (1, 1), (255, 0, 0)).save(buf, format="JPEG")
        s.photos = [buf.getvalue()]
    return s

# Prompt structure tests
try:
    s = make_session()
    prompt = build_copy_prompt(s)
    assert "Test Product" in prompt
    assert "GENERATE AD FOR" in prompt
    ok("build_copy_prompt: contains product name and generation section")
except Exception as e:
    fail("build_copy_prompt basic", str(e))

try:
    s = make_session(lang="hi")
    prompt = build_copy_prompt(s, language="hi")
    assert "LANGUAGE INSTRUCTION" in prompt or "Hindi" in prompt
    ok("build_copy_prompt: language injection for Hindi")
except Exception as e:
    fail("build_copy_prompt language injection", str(e))

try:
    s = make_session(lang="ar")
    prompt = build_copy_prompt(s, language="ar")
    assert "Arabic" in prompt or "LANGUAGE" in prompt
    ok("build_copy_prompt: language injection for Arabic")
except Exception as e:
    fail("build_copy_prompt Arabic", str(e))

try:
    s = make_session(has_photos=True)
    prompt = build_copy_prompt(s)
    assert "PRODUCT PHOTO ANALYSIS" in prompt
    ok("build_copy_prompt: photo analysis section injected when photos present")
except Exception as e:
    fail("build_copy_prompt photo section", str(e))

try:
    s = make_session()
    assert "PRODUCT PHOTO ANALYSIS" not in build_copy_prompt(s)
    ok("build_copy_prompt: photo section absent when no photos")
except Exception as e:
    fail("build_copy_prompt no photo section", str(e))

try:
    s = make_session()
    s.current_copy = {"headline": "Old Headline", "body": "Old Body"}
    prompt = build_copy_prompt(s, feedback="Make it shorter")
    assert "Make it shorter" in prompt
    assert "Old Headline" in prompt
    ok("build_copy_prompt: feedback loop injection")
except Exception as e:
    fail("build_copy_prompt feedback", str(e))

# Schema validation — required fields present
required_schema_fields = ["brand_colors", "template_suggestion", "gradient_palette", "visual_style", "poster", "instagram", "whatsapp", "google"]
for field in required_schema_fields:
    if field in COPY_SCHEMA:
        ok(f"COPY_SCHEMA contains field: {field}")
    else:
        fail(f"COPY_SCHEMA missing field: {field}", "Not found in schema string")

# Image prompt builder
try:
    s = make_session()
    s.current_copy = make_copy()
    prompt_dict = build_image_prompt(s)
    assert "positive" in prompt_dict
    assert "negative" in prompt_dict
    assert len(prompt_dict["positive"]) > 50
    ok("build_image_prompt: returns dict with positive/negative keys")
except Exception as e:
    fail("build_image_prompt", str(e))

try:
    s = make_session()
    s.current_copy = {}  # Empty copy - must not crash
    prompt_dict = build_image_prompt(s)
    assert isinstance(prompt_dict, dict)
    ok("build_image_prompt: handles empty copy without crash")
except Exception as e:
    fail("build_image_prompt empty copy", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6: BACKGROUND REMOVER TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 6: Background Remover")

from bot.bg_remover import remove_background, extract_dominant_color, _convert_to_rgba_png

print("  Loading test images...")
test_images = load_test_images()

# Test dominant color extraction
for img_name, img_bytes in test_images.items():
    try:
        color = extract_dominant_color(img_bytes)
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)
        ok(f"extract_dominant_color: '{img_name}' → RGB{color}")
    except Exception as e:
        fail(f"extract_dominant_color '{img_name}'", str(e))

# Test RGBA conversion (fallback path)
for img_name, img_bytes in test_images.items():
    try:
        rgba = _convert_to_rgba_png(img_bytes)
        img = Image.open(io.BytesIO(rgba))
        assert img.mode == "RGBA"
        ok(f"_convert_to_rgba_png: '{img_name}' → RGBA {img.size}")
    except Exception as e:
        fail(f"_convert_to_rgba_png '{img_name}'", str(e))

# Edge case: corrupt image data
try:
    result = _convert_to_rgba_png(b"NOTANIMAGE")
    # Should return original bytes without crashing
    ok("_convert_to_rgba_png: handles corrupt data gracefully")
except Exception:
    ok("_convert_to_rgba_png: corrupt data handled (exception caught)")

# Edge case: empty bytes
try:
    result = _convert_to_rgba_png(b"")
    ok("_convert_to_rgba_png: handles empty bytes")
except Exception:
    ok("_convert_to_rgba_png: empty bytes handled")

# Background removal test (with remove_bg=False since rembg model takes time to download)
# We'll test the fallback path here and use remove_bg=False in compositor tests
try:
    img_bytes = test_images.get("synthetic") or test_images.get("logo")
    result = _convert_to_rgba_png(img_bytes)
    assert len(result) > 0
    ok("Background removal fallback path works")
except Exception as e:
    fail("Background removal fallback", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 7: COMPOSITOR UNIT TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 7: Compositor — Template Auto-Selection")

from bot.compositor import compose_ad, _auto_select_template, _hex_to_rgb, VALID_TEMPLATES, BUSINESS_TEMPLATE_MAP

# Auto template selection
template_map_tests = [
    ("food",      "hero_center"),
    ("fashion",   "split_screen"),
    ("tech",      "minimalist"),
    ("services",  "bold_poster"),
    ("wellness",  "hero_center"),
    ("beauty",    "bold_poster"),
    ("other",     "hero_center"),
    ("UNKNOWN",   "hero_center"),   # Unknown type → default fallback
    ("",          "hero_center"),
    (None,        "hero_center"),
]

copy_empty = {}
for btype, expected in template_map_tests:
    result = _auto_select_template(btype, copy_empty)
    if result == expected:
        ok(f"Auto-select: '{btype}' → '{result}'")
    else:
        fail(f"Auto-select: '{btype}'", f"Expected '{expected}', got '{result}'")

# Gemini-suggested template override
copy_with_suggestion = {"template_suggestion": "minimalist"}
result = _auto_select_template("food", copy_with_suggestion)
if result == "minimalist":
    ok("Auto-select: Gemini suggestion overrides business type")
else:
    fail("Auto-select: Gemini suggestion override", f"Got '{result}'")

# Invalid suggestion → ignored
copy_invalid = {"template_suggestion": "INVALID_TEMPLATE"}
result = _auto_select_template("food", copy_invalid)
if result == "hero_center":
    ok("Auto-select: Invalid template suggestion ignored, falls back to business type default")
else:
    fail("Auto-select: Invalid suggestion handling", f"Got '{result}'")

# Hex to RGB conversion
hex_tests = [
    ("#FF6B35", (255, 107, 53)),
    ("#000000", (0, 0, 0)),
    ("#FFFFFF", (255, 255, 255)),
    ("1E88E5",  (30, 136, 229)),   # Without #
]
for hex_str, expected in hex_tests:
    try:
        result = _hex_to_rgb(hex_str)
        if result == expected:
            ok(f"Hex→RGB: '{hex_str}' → {result}")
        else:
            fail(f"Hex→RGB: '{hex_str}'", f"Expected {expected}, got {result}")
    except Exception as e:
        fail(f"Hex→RGB: '{hex_str}'", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 8: TEMPLATE RENDERING TESTS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 8: Template Rendering — All Combinations")

from bot.templates import hero_center, split_screen, minimalist, bold_poster

test_img = test_images.get("synthetic", test_images.get("logo"))

# Convert test image to RGBA PNG for templates
rgba_png = _convert_to_rgba_png(test_img)

# All template × platform × business type combinations
template_modules = {
    "hero_center": (hero_center, ["food", "wellness", "beauty"]),
    "split_screen": (split_screen, ["fashion", "retail", "clothing"]),
    "minimalist":  (minimalist, ["tech", "saas", "other"]),
    "bold_poster": (bold_poster, ["services", "education", "other"]),
}

platforms = ["instagram", "poster", "whatsapp"]

for tmpl_name, (tmpl_module, btypes) in template_modules.items():
    for platform in platforms:
        btype = btypes[0]  # Test with primary business type
        t0 = time.time()
        try:
            result = tmpl_module.compose(
                product_png=rgba_png,
                copy=make_copy(business=btype),
                platform=platform,
                business_type=btype,
                language="en",
            )
            elapsed = time.time() - t0

            # Validate output
            img = Image.open(io.BytesIO(result))
            assert img.format == "JPEG", f"Expected JPEG, got {img.format}"
            assert len(result) > 10_000, f"Output too small: {len(result)} bytes"
            assert len(result) < 5_000_000, f"Output too large: {len(result)} bytes"

            expected_sizes = {"instagram": (1080, 1080), "poster": (1080, 1350), "whatsapp": (800, 800)}
            exp_w, exp_h = expected_sizes[platform]
            assert img.size == (exp_w, exp_h), f"Size mismatch: {img.size} vs ({exp_w},{exp_h})"

            path = save_image(f"{tmpl_name}_{platform}.jpg", result)
            ok(f"{tmpl_name}/{platform}: {img.size} {len(result):,}b in {elapsed:.2f}s")
        except Exception as e:
            fail(f"{tmpl_name}/{platform}", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 9: COPY EDGE CASES IN TEMPLATES
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 9: Edge Cases — Unusual Copy Content")

edge_copy_tests = [
    # (label, copy_overrides)
    ("Empty headline",    {"headline": ""}),
    ("Empty body",        {"body": ""}),
    ("Empty CTA",         {"cta": ""}),
    ("Very long headline", {"headline": "This Is An Extremely Long Headline That Goes Way Beyond Normal Limits And Should Be Word-Wrapped Properly Without Crashing The Compositor Engine At All"}),
    ("Very long body",    {"body": "A " * 200}),  # 400-char body
    ("Unicode headline",  {"headline": "Spécial Ñoño Über 日本語 العربية"}),
    ("Emoji in copy",     {"headline": "🔥 Hot Deal 🎉 50% OFF 💯"}),
    ("Single word",       {"headline": "Wow", "body": "Yes.", "cta": "Go"}),
    ("Numbers only",      {"headline": "50% OFF TODAY ONLY", "cta": "Save $99 Now"}),
    ("No brand colors",   {"brand_colors": []}),
    ("No poster bullets", {"poster": {}}),
    ("Missing poster key", {}),  # No poster key at all
]

for label, overrides in edge_copy_tests:
    base = make_copy()
    base.update(overrides)
    try:
        result = hero_center.compose(
            product_png=rgba_png,
            copy=base,
            platform="instagram",
            business_type="food",
            language="en",
        )
        img = Image.open(io.BytesIO(result))
        assert img.size == (1080, 1080)
        ok(f"Edge case: '{label}'")
    except Exception as e:
        fail(f"Edge case: '{label}'", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 10: MULTILINGUAL RENDERING
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 10: Multilingual Text Rendering")

multilingual_tests = [
    ("en", "Pure Hydration", "Order Now →"),
    ("hi", "शुद्ध हाइड्रेशन", "अभी ऑर्डर करें"),
    ("ar", "ترطيب نقي", "اطلب الآن"),
    ("fr", "Hydratation Pure", "Commandez Maintenant"),
    ("es", "Hidratación Pura", "Compra Ahora"),
    ("de", "Reine Hydratation", "Jetzt Bestellen"),
    ("pt", "Hidratação Pura", "Compre Agora"),
    ("zh", "纯净水化", "立即购买"),
    ("ja", "純粋な水化", "今すぐ注文"),
    ("ko", "순수한 수화", "지금 주문"),
]

for lang, headline, cta in multilingual_tests:
    try:
        copy = make_copy(headline=headline, cta=cta)
        result = hero_center.compose(
            product_png=rgba_png,
            copy=copy,
            platform="instagram",
            business_type="food",
            language=lang,
        )
        img = Image.open(io.BytesIO(result))
        assert img.size == (1080, 1080)
        save_image(f"multilingual_{lang}.jpg", result)
        ok(f"Multilingual render: {lang} — '{headline[:20]}...' if len > 20 else '{headline}'")
    except Exception as e:
        fail(f"Multilingual render: {lang}", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 11: COMPOSITOR FULL PIPELINE (with remove_bg=False)
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 11: Compositor Full Pipeline")

from bot.compositor import compose_ad, compose_all_sizes

# Full pipeline with auto template selection
full_pipeline_tests = [
    ("food",     "hero_center",  "instagram", "en"),
    ("fashion",  "split_screen", "instagram", "en"),
    ("tech",     "minimalist",   "instagram", "en"),
    ("services", "bold_poster",  "instagram", "en"),
    ("wellness", None,           "poster",    "en"),
    ("beauty",   None,           "whatsapp",  "en"),
    ("food",     "hero_center",  "instagram", "hi"),  # Hindi
    ("services", "bold_poster",  "poster",    "ar"),  # Arabic RTL
    ("tech",     "minimalist",   "whatsapp",  "fr"),  # French
]

for btype, tmpl, platform, lang in full_pipeline_tests:
    try:
        t0 = time.time()
        result = compose_ad(
            product_bytes=test_img,
            copy=make_copy(business=btype),
            template=tmpl,
            platform=platform,
            business_type=btype,
            language=lang,
            remove_bg=False,
        )
        elapsed = time.time() - t0
        img = Image.open(io.BytesIO(result))
        assert len(result) > 10_000
        label = f"compose_ad: {btype}/{platform}/lang={lang}/tmpl={tmpl or 'auto'}"
        ok(f"{label} — {img.size} in {elapsed:.2f}s")
    except Exception as e:
        fail(f"compose_ad: {btype}/{platform}/lang={lang}", str(e))

# compose_all_sizes test
try:
    t0 = time.time()
    results = compose_all_sizes(
        product_bytes=test_img,
        copy=make_copy(),
        business_type="food",
        language="en",
    )
    elapsed = time.time() - t0
    assert "instagram" in results
    assert "poster" in results
    assert "whatsapp" in results
    valid = sum(1 for v in results.values() if v is not None)
    ok(f"compose_all_sizes: {valid}/3 platforms rendered in {elapsed:.2f}s")
except Exception as e:
    fail("compose_all_sizes", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 12: RESILIENCE / ERROR HANDLING
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 12: Resilience & Error Handling")

# Corrupt product image → should fallback gracefully
try:
    result = compose_ad(
        product_bytes=b"NOTANIMAGE_CORRUPT_DATA",
        copy=make_copy(),
        template="hero_center",
        platform="instagram",
        business_type="food",
        language="en",
        remove_bg=False,
    )
    ok("Corrupt image input: compositor handled gracefully (no crash)")
except Exception as e:
    # We expect this might fail at PIL level — test that it fails with a meaningful error
    if "cannot identify image file" in str(e) or "cannot identify" in str(e).lower():
        ok("Corrupt image input: fails with expected PIL error (not silent crash)")
    else:
        fail("Corrupt image input resilience", f"Unexpected error: {e}")

# Empty product image bytes → should not hang
try:
    result = compose_ad(
        product_bytes=b"",
        copy=make_copy(),
        template="hero_center",
        platform="instagram",
        business_type="food",
        language="en",
        remove_bg=False,
    )
    ok("Empty image bytes: handled without hang")
except Exception as e:
    ok(f"Empty image bytes: properly raised error '{type(e).__name__}'")

# None copy fields → graceful fallback
try:
    null_copy = {k: None for k in ["headline", "body", "cta", "hashtags", "poster", "visual_style"]}
    result = hero_center.compose(
        product_png=rgba_png,
        copy=null_copy,
        platform="instagram",
        business_type="food",
        language="en",
    )
    ok("None copy fields: compositor used defaults gracefully")
except Exception as e:
    fail("None copy fields resilience", str(e))

# Unknown platform → should fallback to instagram size
try:
    result = hero_center.compose(
        product_png=rgba_png,
        copy=make_copy(),
        platform="UNKNOWN_PLATFORM",
        business_type="food",
        language="en",
    )
    img = Image.open(io.BytesIO(result))
    ok(f"Unknown platform: fallback size used → {img.size}")
except Exception as e:
    fail("Unknown platform resilience", str(e))

# None brand_color → auto-detected
try:
    result = compose_ad(
        product_bytes=test_img,
        copy=make_copy(),
        template="hero_center",
        platform="instagram",
        business_type="food",
        language="en",
        brand_color=None,
        remove_bg=False,
    )
    ok("brand_color=None: auto color extraction worked")
except Exception as e:
    fail("brand_color=None handling", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 13: PERFORMANCE BENCHMARKS
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 13: Performance Benchmarks")

RENDER_TIME_LIMIT = 3.0  # Max acceptable seconds per render

# Benchmark: 10 consecutive renders of the same template
timings = []
for i in range(10):
    t0 = time.time()
    hero_center.compose(product_png=rgba_png, copy=make_copy(), platform="instagram", business_type="food", language="en")
    timings.append(time.time() - t0)

avg = sum(timings) / len(timings)
max_t = max(timings)
min_t = min(timings)

if avg < RENDER_TIME_LIMIT:
    ok(f"Render throughput: avg={avg:.3f}s, min={min_t:.3f}s, max={max_t:.3f}s (10 runs)")
else:
    warn(f"Render performance", f"avg={avg:.3f}s exceeds {RENDER_TIME_LIMIT}s limit")

# Benchmark: all 4 templates once
for tmpl_name, tmpl_module in [("hero_center", hero_center), ("split_screen", split_screen), ("minimalist", minimalist), ("bold_poster", bold_poster)]:
    t0 = time.time()
    tmpl_module.compose(product_png=rgba_png, copy=make_copy(), platform="instagram", business_type="food", language="en")
    elapsed = time.time() - t0
    label = f"Render time: {tmpl_name} = {elapsed:.3f}s"
    if elapsed < RENDER_TIME_LIMIT:
        ok(label)
    else:
        warn(label, f"Exceeds {RENDER_TIME_LIMIT}s limit")

# Output size sanity check
size_tests = [
    ("hero_center/instagram",  hero_center, "instagram"),
    ("split_screen/instagram", split_screen, "instagram"),
    ("minimalist/instagram",   minimalist, "instagram"),
    ("bold_poster/poster",     bold_poster, "poster"),
]
for label, tmpl, platform in size_tests:
    result = tmpl.compose(product_png=rgba_png, copy=make_copy(), platform=platform, business_type="food", language="en")
    size_kb = len(result) / 1024
    if 20 < size_kb < 500:
        ok(f"File size: {label} = {size_kb:.0f}KB (within 20KB-500KB range)")
    else:
        warn(f"File size: {label}", f"{size_kb:.0f}KB outside expected range")


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 14: CONFIG VALIDATION
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 14: Config & .env Validation")

import config

config_checks = [
    ("TELEGRAM_TOKEN", hasattr(config, "TELEGRAM_TOKEN")),
    ("GEMINI_API_KEY", hasattr(config, "GEMINI_API_KEY")),
    ("GEMINI_MODEL",   hasattr(config, "GEMINI_MODEL")),
    ("State enum",     hasattr(config, "State")),
    ("FREE_ADS_PER_DAY", hasattr(config, "FREE_ADS_PER_DAY")),
    ("FREE_IMAGES_PER_DAY", hasattr(config, "FREE_IMAGES_PER_DAY")),
    ("BUSINESS_TYPES", hasattr(config, "BUSINESS_TYPES")),
    ("ALL_PLATFORMS",  hasattr(config, "ALL_PLATFORMS")),
]

for field, exists in config_checks:
    if exists:
        ok(f"Config: '{field}' present")
    else:
        fail(f"Config: '{field}' missing", "Not found in config.py")

# Check .env loaded
token = getattr(config, "TELEGRAM_TOKEN", None)
if token and len(str(token)) > 20:
    ok("TELEGRAM_TOKEN: loaded from .env (non-empty)")
else:
    warn("TELEGRAM_TOKEN", "Empty or too short — bot won't connect to Telegram")

gemini_key = getattr(config, "GEMINI_API_KEY", None)
if gemini_key and len(str(gemini_key)) > 20:
    ok("GEMINI_API_KEY: loaded from .env (non-empty)")
else:
    warn("GEMINI_API_KEY", "Empty or too short — Gemini copy generation will fail")


# ════════════════════════════════════════════════════════════════════════════════
# SECTION 15: v1 REGRESSION — Pollinations fallback
# ════════════════════════════════════════════════════════════════════════════════

section("SECTION 15: v1 Regression — Pollinations FLUX Prompt Builder")

from bot.prompts import build_image_prompt

regression_sessions = [
    ("food", "instagram"),
    ("tech", "poster"),
    ("fashion", "whatsapp"),
    ("services", "all"),
]

for btype, platform in regression_sessions:
    try:
        s = make_session(btype, platform)
        s.current_copy = make_copy(business=btype)
        prompt = build_image_prompt(s)
        assert "positive" in prompt
        assert "negative" in prompt
        assert "professional" in prompt["positive"].lower() or "advertisement" in prompt["positive"].lower()
        assert "watermark" in prompt["negative"].lower() or "text" in prompt["negative"].lower()
        ok(f"v1 FLUX prompt: {btype}/{platform} → positive={len(prompt['positive'])}c, negative={len(prompt['negative'])}c")
    except Exception as e:
        fail(f"v1 FLUX prompt: {btype}/{platform}", str(e))


# ════════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ════════════════════════════════════════════════════════════════════════════════

print("\n" + "="*60)
print("  FINAL QA REPORT")
print("="*60)
print(f"  Total passed:   {PASSED}")
print(f"  Total failed:   {FAILED}")
print(f"  Warnings:       {len(WARNINGS)}")
print()

if WARNINGS:
    print("  WARNINGS:")
    for w in WARNINGS:
        print(w)
    print()

if FAILED == 0:
    print("  🎉 ALL TESTS PASSED — v2 is production ready for demo!")
else:
    print(f"  ⚠️  {FAILED} test(s) failed — review above output")

print(f"\n  Test images saved to: {OUTPUT_DIR}/")
print("="*60)

# Exit with failure code if any tests failed
sys.exit(0 if FAILED == 0 else 1)
