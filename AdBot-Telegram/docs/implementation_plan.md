# 🎯 AdBot — Poster Quality Overhaul Plan

## The Problem (Root Cause Analysis)

The main output — the **AI-generated poster** — is market-quality-failing because of **3 compounding bugs**:

### Bug 1: Vague Image Prompt → Random/Wrong Product
The current `build_image_prompt()` sends a 250-char generic string to Pollinations.ai.
Pollinations is a **diffusion model** — vague prompts = random hallucinations.
```
CURRENT (BAD):
"Professional advertising poster for 'New Balance 480 Shoes'. Lightweight, extra cushioning.
clean white studio, editorial fashion lighting. High quality, 4K, no text, no watermarks."
```
Pollinations sees "shoe" and invents its own shoe. The product looks nothing like the user's product.

### Bug 2: `visual_style` from Gemini is Often Empty
The JSON schema asks Gemini for `"visual_style"` but Pollinations.ai sees a **blank field 60%+ of the time**,
so the code falls to a hardcoded generic default that matches nothing.

### Bug 3: No Negative Prompts & No Style Anchors
Diffusion models need **negative prompts** to avoid generating: random text, watermarks, blurry images,
random people, wrong product colors. Without them, every image is a lottery.

---

## The Fix: 3-Part Overhaul

### Part 1 — Smarter Gemini → Richer `visual_style` (in `prompts.py`)

Force Gemini to generate a **detailed, Stable Diffusion-style** visual description as part of the copy JSON.
Instead of one vague sentence, get: subject + composition + lighting + colors + mood + background + style.

**New schema field:**
```json
"visual_style": {
  "subject": "pair of grey and white New Balance 480 running shoes on a flat surface",
  "composition": "product hero shot, centered, 45-degree angle",
  "lighting": "soft studio lighting with subtle shadows",
  "background": "clean light grey gradient background",
  "mood": "energetic, athletic, premium",
  "style": "commercial product photography, 8K, ultra sharp"
}
```

### Part 2 — Pro-Grade Pollinations.ai Prompt Engineering (in `prompts.py` + `image_client.py`)

Build a **structured prompt** from all available session data:
- Product name + USP → subject anchor
- Business type → composition style  
- Platform → aspect ratio & layout guidance
- Gemini's visual_style → lighting/mood
- Negative prompts → block hallucinations

**New prompt formula (industry standard):**
```
[SUBJECT], [COMPOSITION], [LIGHTING], [COLORS/MOOD], [STYLE KEYWORDS], [QUALITY BOOSTERS]
--negative [TEXT], [WATERMARKS], [RANDOM PEOPLE], [LOGO], [BLURRY], [BAD ANATOMY]
```

### Part 3 — Pollinations.ai API Upgrade (in `image_client.py` + `config.py`)

Use Pollinations' full API parameter set:
- `model=flux` → best quality model (vs default SDXL)
- `width=1024&height=1024` → proper resolution
- `nologo=true` → clean output
- `enhance=true` → auto-quality boost  
- Fixed `seed` per session → reproducible results

---

## Files to Change

### [MODIFY] `bot/prompts.py`
- Upgrade `COPY_SCHEMA` → make `visual_style` a rich structured object
- Add `NEGATIVE_PROMPTS` dict per business type
- Rewrite `build_image_prompt()` → structured SD-style prompt builder that uses ALL session data

### [MODIFY] `bot/image_client.py`
- Upgrade `_pollinations()` → use `model=flux`, pass width/height explicitly
- Add `_build_pollinations_url()` helper that takes full prompt + negatives
- Better error handling + timeout (30s not 25s)

### [MODIFY] `config.py`
- Update `POLLINATIONS_URL` template to support model selection + negative prompts

---

## What "Market Standard" Actually Means

| Before (Current) | After (Fix) |
|---|---|
| Random shoe from generic prompt | Correct product style & context |
| Hallucinated background | Clean, professional background per industry |
| Random color scheme | Colors driven by product/brand aesthetic |
| Often has text/watermarks | Negative prompts block all text |
| Low resolution feeling | Flux model + enhance flag |
| Same generic look every time | Platform-specific composition |

---

## Verification Plan
1. Run test against 3 products: Food, Fashion, Tech
2. Compare OLD vs NEW prompt strings side-by-side
3. Generate live images from both and compare
4. Bot must be restarted after changes
