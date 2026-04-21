"""
bot/prompts.py — Few-shot prompt templates, organised by business type.

Each industry has 2-3 curated example ads so that Gemini can pattern-match
to produce high-quality output on the first attempt.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Few-shot examples per industry
# ─────────────────────────────────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = {
    "food": """
EXAMPLE 1 (Food — Artisan Coffee):
Product: Handcrafted cold brew coffee | USP: 24-hour slow-steeped, zero bitterness | Audience: urban professionals 25-40
Output ad:
- Headline: "Coffee That Doesn't Compromise"
- Body: "Why chase sleep when you can sip smooth? Our 24-hour cold brew delivers pure, bold flavour without the bite. Made for people who hustle hard — and taste harder."
- CTA: "Order your first batch →"
- Hashtags: #ColdBrew #CoffeeCulture #SpecialtyCoffee

EXAMPLE 2 (Food — Home Baker):
Product: Eggless chocolate fudge cake | USP: 100% vegan, tastes better than regular cake | Audience: health-conscious families
Output ad:
- Headline: "You Won't Believe It's Vegan"
- Body: "Rich, moist, and guilt-free. Our eggless chocolate fudge cake is proof that you don't need eggs to make something incredible. Perfect for birthdays, gifting, or just because."
- CTA: "Order a slice (or a whole one 🎂)"
- Hashtags: #VeganCake #EgglessBaking #HealthyTreats
""",

    "fashion": """
EXAMPLE 1 (Fashion — Handloom Sarees):
Product: Hand-woven Banarasi silk sarees | USP: 6-yard stories, woven by master artisans, zero machine touch | Audience: women 28-55, tradition-conscious
Output ad:
- Headline: "Wear a Legacy, Not Just a Saree"
- Body: "Every thread tells a story centuries in the making. Our Banarasi handlooms are crafted by master weavers using age-old techniques — because some things are too precious to rush."
- CTA: "Explore the collection"
- Hashtags: #Banarasi #HandloomIndia #EthnicWear

EXAMPLE 2 (Fashion — Streetwear):
Product: Gender-neutral oversized hoodies | USP: Premium 400GSM cotton, never shrinks | Audience: Gen Z & millennials 16-30
Output ad:
- Headline: "Drip That Hits Different"
- Body: "Heavy. Soft. Built to outlast trends. Our 400GSM oversized fits are the only hoodie you'll ever need — wear it your way, any day."
- CTA: "Shop the drop ↗"
- Hashtags: #Streetwear #OversizedFit #OOTD
""",

    "tech": """
EXAMPLE 1 (Tech — Phone Repair Service):
Product: Same-day smartphone screen replacement | USP: Doorstep pickup, 90-day warranty, OEM parts | Audience: smartphone users 18-45
Output ad:
- Headline: "Fixed Before Dinner. Guaranteed."
- Body: "Cracked screen ruining your day? We come to you, fix it in 30 minutes, and back it with a 90-day warranty. OEM parts. No shortcuts."
- CTA: "Book a pickup now →"
- Hashtags: #PhoneRepair #SameDayService #ScreenReplacement

EXAMPLE 2 (Tech — Online Course):
Product: 8-week Python for beginners course | USP: Job-ready portfolio in 8 weeks, 1:1 mentor support | Audience: career changers 22-40
Output ad:
- Headline: "8 Weeks to Job-Ready Python"
- Body: "No CS degree. No jargon. Just real skills. Our mentored Python bootcamp gets you from zero to a working portfolio — the kind that actually gets you hired."
- CTA: "Start free for 7 days"
- Hashtags: #LearnPython #TechCareer #CodingBootcamp
""",

    "services": """
EXAMPLE 1 (Services — Home Cleaning):
Product: Premium home deep-cleaning service | USP: Eco-friendly products, 5-star rated team, satisfaction guarantee | Audience: working families, 28-50
Output ad:
- Headline: "Come Home to Spotless."
- Body: "Life's too short to spend weekends scrubbing. Our eco-certified team handles everything — deep clean, sanitise, done. You relax; we take care of the rest."
- CTA: "Book your first clean at 20% off →"
- Hashtags: #HomeCleaning #EcoCleaning #CleanHome

EXAMPLE 2 (Services — Digital Marketing Agency):
Product: Social media management for small businesses | USP: Done-for-you content, guaranteed 2x engagement in 60 days | Audience: small business owners 30-55
Output ad:
- Headline: "Let Your Socials Work While You Don't"
- Body: "Posting every day and still getting crickets? We create thumb-stopping content, manage your DMs, and get you real engagement — guaranteed, or your money back."
- CTA: "Get your free audit →"
- Hashtags: #SocialMediaMarketing #SmallBusinessGrowth #ContentStrategy
""",

    "other": """
EXAMPLE 1 (General Product Ad):
Product: [Product Name] | USP: [Key differentiator] | Audience: [Target group]
Output ad:
- Headline: Focus on the #1 benefit, 6-10 words max
- Body: 2-3 punchy sentences addressing the pain point, then the solution
- CTA: Action verb + specific outcome (not generic "Buy Now")
- Hashtags: 3 relevant niche hashtags
""",
}

# ─────────────────────────────────────────────────────────────────────────────
# Platform-specific guidelines injected into the prompt
# ─────────────────────────────────────────────────────────────────────────────

PLATFORM_GUIDELINES = {
    "instagram": "Format for Instagram: headline ≤10 words, punchy body 2-3 sentences, emojis welcome, 3-5 hashtags. Tone: aspirational & visual.",
    "whatsapp": "Format for WhatsApp forward: conversational tone, feel personal/local, under 150 words total, no hashtags, include a phone-CTA like 'Message us: [link]'",
    "google": "Format for Google Ad: Headline 1 (max 30 chars), Headline 2 (max 30 chars), Headline 3 (max 30 chars), Description 1 (max 90 chars), Description 2 (max 90 chars). No emojis.",
    "poster": "Format for print poster: Bold headline (6 words max), supporting tagline (10 words max), 3 bullet benefits, strong CTA. No hashtags.",
    "all": "Generate ALL four versions: Instagram, WhatsApp, Google Ad, and Print Poster.",
}

# ─────────────────────────────────────────────────────────────────────────────
# Master prompt builder
# ─────────────────────────────────────────────────────────────────────────────

AD_COPY_SCHEMA = """
Return ONLY valid JSON (no markdown, no explanation). Schema:
{
  "headline": "Main headline",
  "body": "Main body copy",
  "cta": "Call-to-action text",
  "hashtags": ["tag1", "tag2", "tag3"],
  "audience_description": "One sentence describing the ideal customer",
  "ab_variation": "An alternative headline to A/B test",
  "visual_style": "One sentence describing the ideal visual style / colours / mood for the poster image",

  "instagram": { "headline": "...", "body": "...", "cta": "...", "hashtags": ["..."] },
  "whatsapp":  { "body": "..." },
  "google":    { "h1": "...", "h2": "...", "h3": "...", "d1": "...", "d2": "..." },
  "poster":    { "headline": "...", "tagline": "...", "bullets": ["...", "...", "..."], "cta": "..." }
}
"""


def build_copy_prompt(session, feedback: str = "") -> str:
    """
    Build the full Gemini prompt for ad copy generation.
    Combines few-shot examples + CoT instruction + platform guidelines.
    """
    btype = session.business_type or "other"
    examples = FEW_SHOT_EXAMPLES.get(btype, FEW_SHOT_EXAMPLES["other"])
    platform_note = PLATFORM_GUIDELINES.get(session.platform, PLATFORM_GUIDELINES["all"])

    feedback_section = ""
    if feedback and session.current_copy:
        feedback_section = f"""
PREVIOUS AD (user rated it low):
Headline: {session.current_copy.get('headline','')}
Body: {session.current_copy.get('body','')}

USER FEEDBACK: "{feedback}"
Please address this feedback specifically in the new version.
"""

    has_photo_hint = "The user has also provided product photos — let those visuals influence the tone and imagery in the copy." if session.photos else ""

    prompt = f"""You are an expert advertising copywriter specialising in {btype} businesses.
Use chain-of-thought reasoning internally before writing — think about the audience's pain point, then the product solution, then the emotional hook.

Here are excellent example ads for this industry (use these as style inspiration, NOT as templates to copy):
{examples}

--- NOW GENERATE AN AD FOR THIS PRODUCT ---

Product Name: {session.product_name}
Product Details: {session.product_details}
Unique Selling Proposition (USP): {session.usp}
Target Audience: {session.audience}
{has_photo_hint}

Platform requirement: {platform_note}
{feedback_section}

{AD_COPY_SCHEMA}
"""
    return prompt.strip()


def build_image_prompt(session) -> str:
    """
    Build the SDXL/Pollinations image generation prompt.
    If visual_style is already set from Gemini's output, use it.
    Otherwise generate a sensible default based on business type.
    """
    visual_style = session.current_copy.get("visual_style", "")
    product = session.product_name
    usp = session.usp
    btype = session.business_type

    style_defaults = {
        "food": "warm golden lighting, food photography style, shallow depth of field, rustic wooden background",
        "fashion": "clean white studio background, model wearing the product, high fashion editorial lighting",
        "tech": "minimalist dark background, blue accent lighting, product hero shot, clean and modern",
        "services": "professional, friendly, bright natural lighting, real people in action",
        "other": "clean product shot, professional studio lighting, vibrant colours",
    }

    style = visual_style if visual_style else style_defaults.get(btype, style_defaults["other"])

    return (
        f"Professional advertising poster for '{product}'. {usp}. "
        f"{style}. High quality, commercial photography, 4K, advertising campaign, "
        f"no text, no watermarks, no logos."
    )
