"""
bot/prompts.py — Industry-specific prompts, schemas, and image prompt builder.

ARCHITECTURE NOTE (Image Quality):
    The old version sent a vague ~250-char string to Pollinations → random/wrong products.

    New pipeline (2-stage "Vision DNA" approach):
    ┌──────────────────────────────────────────────────────────────────────┐
    │  Stage 1 (Gemini Vision):                                            │
    │    User's product photo → Gemini analyzes → extracts exact product   │
    │    DNA: colors, materials, shape, texture, distinctive features      │
    │    This is stored in copy JSON as visual_style (a rich dict)         │
    │                                                                      │
    │  Stage 2 (Pollinations FLUX):                                        │
    │    visual_style dict → build_image_prompt() → professional SD prompt │
    │    Positive prompt: subject + composition + lighting + mood          │
    │    Negative prompt: blocks text, watermarks, bad anatomy             │
    │    → Pollinations.ai FLUX generates the ad poster                   │
    └──────────────────────────────────────────────────────────────────────┘

    Result: Images that match the actual product (not a random hallucination).
"""


# ── Few-shot examples per industry ───────────────────────────────────────────
# These show Gemini what HIGH-QUALITY ad copy looks like for each industry.
# "Few-shot" means we give examples BEFORE asking it to generate — this is a
# core prompt engineering technique that dramatically improves first-gen quality.

FEW_SHOT_EXAMPLES = {
    "food": """
EXAMPLE 1 — Artisan Cold Brew Coffee:
Product: Handcrafted cold brew | USP: 24-hour slow-steeped, zero bitterness | Audience: urban professionals 25-40
Headline: "Coffee That Doesn't Compromise"
Body: "Why chase sleep when you can sip smooth? Our 24-hour cold brew delivers pure, bold flavour without the bite. Made for people who hustle hard — and taste harder."
CTA: "Order your first batch →"
Hashtags: ColdBrew, CoffeeCulture, SpecialtyCoffee

EXAMPLE 2 — Eggless Vegan Bakery:
Product: Eggless chocolate fudge cake | USP: 100% vegan, tastes better than regular cake | Audience: health-conscious families
Headline: "You Won't Believe It's Vegan"
Body: "Rich, moist, and guilt-free. Our eggless fudge cake proves you don't need eggs to make something incredible."
CTA: "Order a slice (or a whole one 🎂)"
Hashtags: VeganCake, EgglessBaking, HealthyTreats
""",
    "fashion": """
EXAMPLE 1 — Handloom Sarees:
Product: Hand-woven Banarasi silk sarees | USP: Zero machine touch, master artisans | Audience: women 28-55
Headline: "Wear a Legacy, Not Just a Saree"
Body: "Every thread tells a story centuries in the making. Crafted by master weavers using age-old techniques."
CTA: "Explore the collection"
Hashtags: Banarasi, HandloomIndia, EthnicWear

EXAMPLE 2 — Streetwear:
Product: Gender-neutral oversized hoodies | USP: 400GSM cotton, never shrinks | Audience: Gen Z 16-30
Headline: "Drip That Hits Different"
Body: "Heavy. Soft. Built to outlast trends. The only hoodie you'll ever need."
CTA: "Shop the drop ↗"
Hashtags: Streetwear, OversizedFit, OOTD
""",
    "tech": """
EXAMPLE 1 — Phone Repair:
Product: Same-day screen replacement | USP: Doorstep pickup, 90-day warranty | Audience: smartphone users 18-45
Headline: "Fixed Before Dinner. Guaranteed."
Body: "Cracked screen ruining your day? We come to you, fix in 30 minutes, 90-day warranty. OEM parts only."
CTA: "Book a pickup now →"
Hashtags: PhoneRepair, SameDayService, ScreenReplacement

EXAMPLE 2 — Online Course:
Product: 8-week Python bootcamp | USP: Portfolio in 8 weeks, 1:1 mentor | Audience: career changers 22-40
Headline: "8 Weeks to Job-Ready Python"
Body: "No CS degree. No jargon. Just real skills that get you hired."
CTA: "Start free for 7 days"
Hashtags: LearnPython, TechCareer, CodingBootcamp
""",
    "services": """
EXAMPLE 1 — Home Cleaning:
Product: Eco deep-clean service | USP: Eco-certified, satisfaction guarantee | Audience: working families 28-50
Headline: "Come Home to Spotless."
Body: "Life's too short to spend weekends scrubbing. Our eco-certified team handles everything."
CTA: "Book at 20% off →"
Hashtags: HomeCleaning, EcoCleaning, CleanHome

EXAMPLE 2 — Marketing Agency:
Product: Social media management | USP: Guaranteed 2x engagement in 60 days | Audience: SMBs 30-55
Headline: "Let Your Socials Work While You Don't"
Body: "We create thumb-stopping content and get you real engagement — guaranteed or money back."
CTA: "Get your free audit →"
Hashtags: SocialMedia, SmallBusiness, ContentStrategy
""",
    "other": """
EXAMPLE — Generic Product:
Headline: Focus on the #1 benefit, 6-10 words
Body: Pain point → solution → emotional hook, 2-3 punchy sentences
CTA: Action verb + specific outcome (never generic "Buy Now")
Hashtags: 3 niche hashtags
""",
}


# ── Platform copy guidelines ─────────────────────────────────────────────────
# Tells Gemini the rules for each ad format.
PLATFORM_GUIDELINES = {
    "instagram": "Instagram Post: headline ≤10 words, punchy body 2-3 sentences, emojis welcome, 3-5 hashtags. Tone: aspirational & visual.",
    "whatsapp":  "WhatsApp: conversational, personal/local feel, ≤150 words, NO hashtags, include 'Message us' or phone CTA.",
    "google":    "Google Ad: H1 (≤30 chars), H2 (≤30 chars), H3 (≤30 chars), D1 (≤90 chars), D2 (≤90 chars). No emojis.",
    "poster":    "Print Poster: bold headline (≤6 words), tagline (≤10 words), 3 bullet benefits, strong CTA. No hashtags.",
    "all":       "Generate ALL FOUR versions: Instagram Post, WhatsApp message, Google Ad, Print Poster.",
}


# ── JSON Schema returned by Gemini ───────────────────────────────────────────
# IMPORTANT DESIGN RULE: Keep the JSON structure clean with SHORT placeholder values.
# Never put long instruction text inside the JSON template values — it confuses Gemini
# into outputting those instruction strings literally, causing JSONDecodeError.
# Field guidance goes BELOW the JSON block, as a separate plain-text section.
COPY_SCHEMA = """
Return ONLY valid JSON with no other text, no markdown, no code fences.
Use exactly this structure (replace every "string" with real content):

{
  "headline": "string",
  "body": "string",
  "cta": "string",
  "hashtags": ["string", "string", "string"],
  "audience_description": "string",
  "ab_variation": "string",
  "visual_style": {
    "subject": "string",
    "composition": "string",
    "lighting": "string",
    "background": "string",
    "mood": "string",
    "negative": "string"
  },
  "instagram": {"headline": "string", "body": "string", "cta": "string", "hashtags": ["string"]},
  "whatsapp":  {"body": "string"},
  "google":    {"h1": "string", "h2": "string", "h3": "string", "d1": "string", "d2": "string"},
  "poster":    {"headline": "string", "tagline": "string", "bullets": ["string", "string", "string"], "cta": "string"}
}

Field guidance for visual_style (this field drives the AI image poster):
- subject:      Exact product description: precise colors (e.g. "matte cream with navy logo"), materials, textures, shape, distinctive features. If photos supplied, describe what you actually SEE in them.
- composition:  Camera framing: e.g. "centered hero shot, 45-degree angle" or "flat-lay top-down"
- lighting:     Lighting: e.g. "soft diffused studio light with drop shadow" or "warm golden hour backlight"
- background:   Background: e.g. "seamless white gradient" or "rustic wooden table, shallow depth of field"
- mood:         Emotional tone: e.g. "energetic and athletic" or "premium and aspirational"
- negative:     What to BLOCK in AI image (always start with): "text, watermark, logo, blurry, low quality"
"""


# ── Negative prompts per business type ───────────────────────────────────────
# These are always included to block common diffusion model failure modes.
# They prevent: random text in image, watermarks, bad anatomy, wrong products.
NEGATIVE_PROMPTS = {
    "food":     "text, watermark, logo, blurry, low quality, overexposed, pixelated, rotten, unappetizing, cartoon, illustration, human hands, person",
    "fashion":  "text, watermark, logo, blurry, low quality, bad anatomy, deformed hands, extra limbs, wrong proportions, ugly, bad skin, disfigured, mutated",
    "tech":     "text, watermark, logo, blurry, scratched, dirty, damaged, low quality, distorted, cartoonish, rust, broken screen",
    "services": "text, watermark, logo, blurry, unprofessional, messy, cluttered, low quality, bad anatomy, deformed",
    "other":    "text, watermark, logo, blurry, low quality, distorted, pixelated, cartoon, illustration",
}

# ── Smart defaults (used when Gemini doesn't fill a visual_style field) ───────
# These are industry-calibrated defaults that produce clean, professional results
# even without a product photo.
_SUBJECT_DEFAULTS = {
    "food":     lambda p, u: f"professional food photography of {p}, {u}, beautifully presented",
    "fashion":  lambda p, u: f"{p}, {u}, apparel product photography",
    "tech":     lambda p, u: f"{p} product hero shot, {u}, sleek and modern device",
    "services": lambda p, u: f"professional service concept for {p}, {u}",
    "other":    lambda p, u: f"product advertisement featuring {p}, {u}",
}

_COMPOSITION_DEFAULTS = {
    "instagram": "centered composition, rule of thirds, square crop friendly",
    "whatsapp":  "clean centered layout, simple and clear",
    "google":    "clean horizontal layout, product visually prominent",
    "poster":    "bold portrait layout, centered composition, ample negative space for text",
    "all":       "centered balanced composition",
}

_LIGHTING_DEFAULTS = {
    "food":     "warm golden studio lighting, soft shadows, appetizing glow",
    "fashion":  "clean diffused studio lighting, subtle rim light, even exposure",
    "tech":     "cool blue-tinted studio lighting, dramatic directional shadows, sleek specular highlights",
    "services": "bright natural daylight, clean and airy, professional atmosphere",
    "other":    "soft studio lighting, clean even shadows, professional",
}

_BACKGROUND_DEFAULTS = {
    "food":     "rustic wooden surface, shallow depth of field blurred background",
    "fashion":  "seamless white or light grey gradient background",
    "tech":     "dark charcoal gradient background, subtle surface reflection",
    "services": "clean bright workspace or office background",
    "other":    "clean neutral gradient background",
}

_MOOD_DEFAULTS = {
    "food":     "warm, appetizing, inviting, fresh, delicious",
    "fashion":  "elegant, stylish, aspirational, premium, confident",
    "tech":     "modern, sleek, innovative, powerful, precise",
    "services": "professional, trustworthy, clean, reliable, competent",
    "other":    "professional, clean, premium, polished, appealing",
}


# ── Public API ────────────────────────────────────────────────────────────────

def build_copy_prompt(session, feedback: str = "") -> str:
    """
    Build the Gemini prompt for ad copy generation.

    When photos are provided, the prompt explicitly instructs Gemini to
    analyze the photos and extract product DNA into visual_style.subject.
    This is Stage 1 of the Vision DNA pipeline.
    """
    btype    = session.business_type or "other"
    examples = FEW_SHOT_EXAMPLES.get(btype, FEW_SHOT_EXAMPLES["other"])
    platform = PLATFORM_GUIDELINES.get(session.platform, PLATFORM_GUIDELINES["all"])

    feedback_section = ""
    if feedback and session.current_copy:
        feedback_section = (
            f"\nPREVIOUS AD (user rated low):\n"
            f"Headline: {session.current_copy.get('headline','')}\n"
            f"Body: {session.current_copy.get('body','')}\n"
            f"USER FEEDBACK: \"{feedback}\"\n"
            f"Address this feedback specifically in the new version.\n"
        )

    # ── Photo analysis instruction (Stage 1: Vision DNA extraction) ──────────
    # When the user has uploaded photos, Gemini's vision model can SEE the
    # product. We instruct it to extract precise visual details so our
    # image generator can reproduce the correct product appearance.
    photo_section = ""
    if session.photos:
        photo_section = """
PRODUCT PHOTO ANALYSIS — REQUIRED:
You have been provided with product photo(s). Examine them carefully.
For the visual_style.subject field, describe EXACTLY what you see:
  • Precise colors (say "matte army green" not just "green")
  • Materials and textures (leather, mesh fabric, brushed metal, matte plastic, glass, etc.)
  • Shape and silhouette (rounded, angular, cylindrical, flat, etc.)
  • Distinctive design features (seams, logos placement, patterns, hardware details)
  • Overall product condition and presentation quality

This description will be fed directly to an AI image generator (Flux/Stable Diffusion).
Think like a professional product photographer writing a shoot brief.
Be specific enough that someone who has NEVER seen this product could reproduce it from your description.
"""

    return f"""You are an expert advertising copywriter for {btype} businesses.
Think step-by-step: audience pain point → product solution → emotional hook → compelling CTA.

Style examples for this industry:
{examples}

{photo_section}
--- GENERATE AD FOR ---
Product: {session.product_name}
Details: {session.product_details}
USP: {session.usp}
Audience: {session.audience}

Platform: {platform}
{feedback_section}
{COPY_SCHEMA}""".strip()


def build_image_prompt(session) -> dict:
    """
    Build a professional image generation prompt from session data.

    Returns a dict with two keys:
      "positive" → the main prompt (what we WANT in the image)
      "negative" → what to EXCLUDE (blocks watermarks, text, bad anatomy, etc.)

    This is Stage 2 of the Vision DNA pipeline:
      - Takes visual_style extracted by Gemini (or smart defaults if empty)
      - Builds a Stable Diffusion / FLUX professional prompt
      - Adds industry-calibrated negative prompts

    Prompt formula (industry standard SD prompt structure):
      [SUBJECT], [COMPOSITION], [LIGHTING], [BACKGROUND], [MOOD],
      [QUALITY BOOSTERS]
    """
    vs    = session.current_copy.get("visual_style", {})
    btype = session.business_type or "other"
    plat  = session.platform or "instagram"

    # Handle backward compatibility: old schema had visual_style as a plain string
    if isinstance(vs, str):
        vs = {"subject": vs} if vs else {}

    product = session.product_name
    usp     = session.usp or ""

    # ── Resolve each prompt component ────────────────────────────────────────
    # Priority: Gemini's extraction > smart business-type default

    subject = (
        vs.get("subject", "").strip()
        or _SUBJECT_DEFAULTS.get(btype, _SUBJECT_DEFAULTS["other"])(product, usp)
    )

    composition = (
        vs.get("composition", "").strip()
        or _COMPOSITION_DEFAULTS.get(plat, _COMPOSITION_DEFAULTS["instagram"])
    )

    lighting = (
        vs.get("lighting", "").strip()
        or _LIGHTING_DEFAULTS.get(btype, _LIGHTING_DEFAULTS["other"])
    )

    background = (
        vs.get("background", "").strip()
        or _BACKGROUND_DEFAULTS.get(btype, _BACKGROUND_DEFAULTS["other"])
    )

    mood = (
        vs.get("mood", "").strip()
        or _MOOD_DEFAULTS.get(btype, _MOOD_DEFAULTS["other"])
    )

    negative = (
        vs.get("negative", "").strip()
        or NEGATIVE_PROMPTS.get(btype, NEGATIVE_PROMPTS["other"])
    )

    # ── Build final positive prompt ───────────────────────────────────────────
    # This format is the industry standard for Stable Diffusion / FLUX prompts.
    # Component order matters: subject first = highest attention weight.
    positive = (
        f"{subject}, "
        f"{composition}, "
        f"{lighting}, "
        f"{background}, "
        f"{mood}, "
        f"professional advertising photography, commercial quality, "
        f"8K ultra sharp focus, highly detailed, no text, no watermark, "
        f"no logo overlay, clean product advertisement"
    )

    return {
        "positive": positive,
        "negative": negative,
    }
