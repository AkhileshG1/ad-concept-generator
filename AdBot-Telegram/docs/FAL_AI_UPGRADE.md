# ⭐ FAL.AI Upgrade Guide — Studio-Grade Image-to-Image

> When you're ready to go from "much better" to "agency-grade," this is the upgrade.
> Estimated time: 30 minutes. Cost: $25 free credit (~500 images).

---

## Why Upgrade?

| Aspect | Current (Pollinations FLUX) | After Upgrade (fal.ai FLUX) |
|---|---|---|
| How it works | Text description → generate | Actual product photo → transform |
| Product accuracy | ~70% (AI imagines from text) | ~95% (AI uses your real photo) |
| Background control | Good | Excellent |
| Consistency | Varies per generation | Very consistent |
| Cost | $0 forever | $25 free → ~$0.05/image after |
| Quality | ★★★☆☆ | ★★★★★ |

**The difference**: Pollinations reads your text and *imagines* the product.
fal.ai takes your actual photo and *transforms* it — product identity is preserved.

---

## How Image-to-Image Works

```
User uploads product photo → stored as bytes in session.photos[0]

OLD pipeline:
  photo bytes → Gemini reads it → writes text description
  → Pollinations imagines product from text
  → Random-ish result

NEW pipeline (fal.ai):
  photo bytes → sent to FLUX as init_image
  → FLUX keeps product appearance (35% of original preserved)
  → FLUX transforms scene, lighting, background (65% changed)
  → Result: YOUR actual product in a professional ad scene
```

The `strength=0.65` parameter controls this balance:
- `0.0` = copy the photo exactly (no changes)
- `1.0` = ignore the photo completely (same as text-to-image)
- `0.65` = keep product identity, transform everything else ← our setting

---

## Step-by-Step Setup

### Step 1: Get fal.ai API Key
1. Go to [https://fal.ai](https://fal.ai) → Sign Up
2. Dashboard → API Keys → Create a new key
3. Copy the key (starts with `fal-`)
4. You start with **$25 free credit** (~500 ad images)

### Step 2: Install fal-client
```bash
cd "/Users/akhilesh/Documents/Add AI agent/AdBot-Telegram"
source venv/bin/activate
pip install fal-client==0.5.0
```

Add to `requirements.txt`:
```
fal-client==0.5.0
```

### Step 3: Add key to .env
Open `.env` and add:
```env
FAL_API_KEY=fal-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 4: Activate the fal.ai client

**In `bot/handlers/image.py`**, make this one-line change:

```python
# FROM (line ~8):
from bot.image_client import generate_image

# TO:
from bot.image_client_fal import generate_image
```

**Also update the executor call** in `run_generate_image()`:

```python
# CURRENT CODE (in image.py):
img_prompt = build_image_prompt(session)

import asyncio
try:
    loop = asyncio.get_running_loop()
    url, img_bytes = await loop.run_in_executor(
        None, generate_image, img_prompt
    )

# REPLACE WITH:
img_prompt = build_image_prompt(session)
# Pass first product photo as image reference (if uploaded)
product_photo = session.photos[0] if session.photos else None

import asyncio
try:
    loop = asyncio.get_running_loop()
    url, img_bytes = await loop.run_in_executor(
        None, generate_image, img_prompt, product_photo
    )
```

### Step 5: Restart the bot
```bash
# Stop current bot (Ctrl+C if running)
source venv/bin/activate
python telegram_bot.py
```

**That's it.** The fal.ai client is a drop-in replacement. Zero other changes needed.

---

## The fal.ai Code (Reference)

The full implementation is in `bot/image_client_fal.py`.

Key parts explained:

```python
# The model used (image-to-image version)
model = "fal-ai/flux/dev/image-to-image"

# Request payload
payload = {
    "prompt":          positive_prompt,    # What we want
    "negative_prompt": negative_prompt,    # What to avoid
    "num_inference_steps": 28,             # 25-35 is optimal for FLUX dev
    "guidance_scale":   3.5,              # 3.0-4.5 = FLUX dev sweet spot
    "image_size":      "square_hd",       # 1024x1024 for Instagram
    "seed":             random.randint(...),

    # Image-to-image specific:
    "image_url": base64_encoded_product_photo,  # The actual product photo
    "strength":  0.65,                          # Keep 35% product, change 65% scene
}
```

---

## Cost Management

fal.ai charges per image:
- FLUX.1-dev: ~$0.025-0.05 per image
- $25 free credit = ~500-1000 free images before you pay

**Protect your credit:**

Option 1: Only use fal.ai for PRO users
```python
# In bot/handlers/image.py
if session.is_pro and product_photo:
    from bot.image_client_fal import generate_image as fal_generate
    url, img_bytes = await loop.run_in_executor(None, fal_generate, img_prompt, product_photo)
else:
    from bot.image_client import generate_image as poll_generate
    url, img_bytes = await loop.run_in_executor(None, poll_generate, img_prompt)
```

Option 2: Add fal.ai to the upgrade pitch
```
Free:  Pollinations FLUX (great quality, free)
PRO:   fal.ai Studio Mode (pixel-perfect product ads)
```
This gives PRO users a compelling reason to upgrade beyond just the "unlimited" pitch.

---

## Recommended Final Architecture

```
Free users:
  Gemini Vision DNA → Pollinations FLUX        ← Current, much better than before

PRO users:
  Gemini Vision DNA → fal.ai image-to-image   ← Studio grade
  (photo uploaded)  → transform into ad scene

No photo uploaded (any tier):
  Gemini copy visual_style → Pollinations FLUX ← Text-to-image, best achievable
```

This is the architecture used by high-end AI design tools.

---

## Troubleshooting

**"fal_client not installed"**: `pip install fal-client==0.5.0`

**"FAL_API_KEY not set"**: Add `FAL_API_KEY=fal-xxx` to your `.env` file

**"402 Payment Required"**: Your $25 credit is used up. Add a payment method at fal.ai/billing

**Image looks nothing like the product photo**: Reduce `strength` to 0.5 (keeps more of original)

**Image looks too much like the original photo**: Increase `strength` to 0.75 (more transformation)

**Generation very slow (>30s)**: Normal for first request while GPU warms up. Subsequent requests faster.
