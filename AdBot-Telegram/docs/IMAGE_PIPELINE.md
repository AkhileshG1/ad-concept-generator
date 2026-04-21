# 🖼️ AdBot — Image Generation Pipeline Deep Dive

> The single most critical quality factor in this bot is the image.
> This document explains the complete evolution from "terrible random images" to "market-standard."

---

## The Problem We Solved

### Why the old images were bad (root cause analysis)

**The old code sent this to Pollinations:**
```
Professional advertising poster for 'New Balance 480 Shoes'. Lightweight, extra cushioning, retro design.
clean white studio, editorial fashion lighting, model wearing product.
High quality, commercial photography, 4K, no text, no watermarks, no logos.
```
**252 characters. vague. generic.**

Pollinations is a **diffusion model** (Stable Diffusion / FLUX). These models work by:
1. Starting with random noise
2. Iteratively removing noise guided by your text prompt

If your prompt is vague → the model fills gaps with its training data → random product.
The model has never seen your product. It imagines what "shoe" looks like from millions of shoe photos.
Result: A random shoe. Often wrong color, wrong style, wrong era.

**Three compounding bugs:**
```
Bug 1: build_image_prompt() built a 252-char vague string
Bug 2: visual_style from Gemini was often "" (empty string) — fell to generic defaults
Bug 3: No negative prompts — model could add text, watermarks, random backgrounds freely
```

---

## The Solution: Vision DNA Pipeline

### What "Vision DNA" means

Real ad agencies work like this:
```
1. Photographer shoots the product (isolated, clean background)
2. Art director writes a "shot brief": colors, mood, composition, background
3. Retoucher composites the product into the final scene
4. Result: The ACTUAL product in a professional ad setting
```

We replicate this digitally:
```
1. User uploads product photo
2. Gemini Vision analyzes it (our "art director") → extracts visual DNA:
   exact colors, materials, shape, distinctive features
3. We build a professional prompt from that DNA
4. Pollinations FLUX generates using that rich prompt
   Result: Much closer to the actual product, professional composition
```

### Why we can't get pixel-perfect results (yet)

Pollinations is **text-to-image** — it generates from scratch guided by text.
No matter how detailed the description, it still imagines the product; it doesn't trace it.

For pixel-perfect results you need **image-to-image** — the model gets the actual photo as input.
→ See `docs/FAL_AI_UPGRADE.md` for this upgrade.

---

## Stage 1: Gemini Vision DNA Extraction

**Where**: `bot/prompts.py` → `build_copy_prompt()` → `photo_section`

**What happens:**
When the user uploads a product photo, we inject this into the Gemini prompt:

```
PRODUCT PHOTO ANALYSIS — REQUIRED:
You have been provided with product photo(s). Examine them carefully.
For the visual_style.subject field, describe EXACTLY what you see:
  • Precise colors (say "matte army green" not just "green")
  • Materials and textures
  • Shape and silhouette
  • Distinctive design features
  • Overall product presentation
```

**What Gemini returns (new `visual_style` dict):**
```json
{
  "visual_style": {
    "subject": "pair of light grey New Balance 480 running shoes with white sole, mesh upper with suede overlays in navy and cream, N logo on side in navy",
    "composition": "product hero shot, shoes tilted 45 degrees, laces visible",
    "lighting": "soft diffused studio lighting with subtle drop shadow beneath",
    "background": "seamless white gradient background, minimal and clean",
    "mood": "athletic, premium, retro-modern, energetic",
    "negative": "text, watermark, logo overlay, blurry, low quality, person, feet"
  }
}
```

**What changed vs before:**
| Before | After |
|---|---|
| `"visual_style": "Clean white studio, editorial fashion lighting"` | Rich 6-field object with product-specific details |
| Always fell to generic defaults | Uses Gemini's actual photo analysis |
| No color/material specifics | Exact colors, materials, features described |
| Script-generated generic phrase | Written by AI that literally SAW the product |

---

## Stage 2: Professional Prompt Assembly

**Where**: `bot/prompts.py` → `build_image_prompt()`

**Priority chain for each field:**
```
1st: Gemini's visual_style extraction (best — based on actual product)
2nd: Smart business-type default (good — industry-calibrated)
3rd: Generic fallback (acceptable — always produces clean result)
```

**Positive prompt structure (industry standard for FLUX/SD):**
```
[SUBJECT], [COMPOSITION], [LIGHTING], [BACKGROUND], [MOOD],
professional advertising photography, commercial quality,
8K ultra sharp focus, highly detailed,
no text, no watermark, no logo overlay, clean product advertisement
```

**Example — Fashion product with photo uploaded:**
```
pair of light grey New Balance 480 running shoes with white sole, mesh upper with suede overlays
in navy and cream, N logo on side in navy,
product hero shot, shoes tilted 45 degrees,
soft diffused studio lighting with subtle drop shadow,
seamless white gradient background,
athletic, premium, retro-modern, energetic,
professional advertising photography, commercial quality, 8K ultra sharp focus,
highly detailed, no text, no watermark, no logo overlay, clean product advertisement
```

vs old:
```
Professional advertising poster for 'New Balance 480 Shoes'. Lightweight...
clean white studio, editorial fashion lighting...
```

**Example — Food product without photo:**
```
professional food photography of Mango Lassi, refreshing summer drink, no artificial additives,
beautifully presented,
centered square composition, rule of thirds,
warm golden studio lighting, soft shadows, appetizing glow,
rustic wooden surface, shallow depth of field blurred background,
warm, appetizing, inviting, fresh, delicious,
professional advertising photography, commercial quality, 8K ultra sharp focus,
no text, no watermark, no logo overlay, clean product advertisement
```

**Negative prompt examples per industry:**
```
Food:    text, watermark, logo, blurry, rotten, unappetizing, cartoon, human hands
Fashion: text, watermark, logo, blurry, bad anatomy, deformed hands, extra limbs
Tech:    text, watermark, logo, blurry, scratched, dirty, broken screen, cartoonish
```

---

## Stage 3: Pollinations FLUX Request

**Where**: `bot/image_client.py` → `_pollinations_flux()`

### FLUX vs SDXL (old model)

| Feature | SDXL (old) | FLUX (new) |
|---|---|---|
| Prompt following | Poor (ignores details) | Excellent (understands complex prompts) |
| Photorealism | Medium | High |
| Negative prompts | Limited | Full support |
| Commercial photography | Generic | Matches description closely |
| Speed | ~8s | ~10s |
| Cost | Free | Free |

### The URL

**Old:**
```
https://image.pollinations.ai/prompt/{simple_text}
  ?width=1024&height=1024&nologo=true&enhance=true&seed={n}
```

**New:**
```
https://image.pollinations.ai/prompt/{detailed_positive_prompt}
  ?model=flux                          ← FLUX model (key change)
  &width=1024
  &height=1024
  &nologo=true                         ← removes Pollinations branding
  &enhance=true                        ← auto quality boost
  &seed={n}                            ← reproducible
  &negative={detailed_negative_prompt} ← blocks bad outputs
```

### Why we return the URL (not download the image)
```python
if "image" in r.headers.get("content-type", ""):
    return url   # Return URL, not bytes
```
With `stream=True`, we check headers only. We give the URL to Telegram, and Telegram
downloads the image directly from Pollinations. This saves:
- Bandwidth (bot never downloads the image)
- Memory (no bytes to hold in RAM)
- Time (parallel download while bot sends other messages)

---

## Current Quality Level

| Scenario | Before | After |
|---|---|---|
| Product with photo | Random wrong product | Correct product description, right style |
| Food without photo | Generic food image | Industry-calibrated warm food photography |
| Fashion without photo | Random clothing | Clean studio editorial style |
| Tech without photo | Random device | Dark sleek product hero shot |
| Text in image | Common (30%+ of images) | Rare (negative prompt blocks it) |
| Watermarks | Common | Blocked by negative prompt |
| Platform-appropriate composition | Never | Always (platform-specific defaults) |

---

## Limitations (What We Can't Do Yet)

1. **Pixel-perfect product**: We describe the product in words, FLUX imagines it.
   Still 10x better, but not identical to actual product.

2. **Complex products**: Intricate jewelry, detailed patterns, specific brand logos
   are hard to describe in words. Vision DNA helps a lot but isn't perfect.

3. **Consistent product across images**: Each generation is fresh. The same product
   may look slightly different across multiple generations.

**Solution to all 3**: → `docs/FAL_AI_UPGRADE.md` (image-to-image pipeline)

---

## Testing the Pipeline

Run this from the project root to see what prompts would be generated:

```bash
source venv/bin/activate && python -c "
import warnings; warnings.filterwarnings('ignore')
from bot.session import UserSession
from bot.prompts import build_image_prompt

# Simulate a fashion session with Gemini output
s = UserSession(1)
s.business_type = 'fashion'
s.platform = 'instagram'
s.product_name = 'Nike Air Force 1'
s.usp = 'Classic all-white leather sneaker, iconic since 1982'
s.current_copy = {
    'visual_style': {
        'subject': 'all-white Nike Air Force 1 low sneaker, smooth white leather upper, perforated toe box, Air cushion visible in heel, clean white rubber sole',
        'composition': 'single shoe centered, slight 45 degree angle, elevated perspective',
        'lighting': 'clean diffused studio lighting, subtle shadow beneath shoe',
        'background': 'pure white seamless background',
        'mood': 'classic, clean, iconic, timeless',
        'negative': 'text, watermark, logo overlay, blurry, dirty, double shoes'
    }
}

result = build_image_prompt(s)
print('POSITIVE:')
print(result['positive'])
print()
print('NEGATIVE:')
print(result['negative'])
"
```
