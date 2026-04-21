"""
bot/image_client.py — Image generation pipeline.

Primary:  Pollinations.ai with FLUX model (free, global, no API key)
Fallback: HuggingFace SDXL-Turbo (requires HF_API_KEY in .env)

KEY UPGRADE (Vision DNA pipeline):
    This module now accepts a DICT prompt instead of a plain string.
    The dict has two keys:
      "positive" → what we WANT  (detailed, structured SD prompt)
      "negative" → what to AVOID (watermarks, text, bad anatomy, etc.)

    This + model=flux gives dramatically better image quality vs the old
    single-string approach with the default SDXL model.

Pollinations.ai FLUX vs old SDXL:
    SDXL (old):  Poor prompt-following, generic outputs, no negative prompt
    FLUX (new):  Excellent prompt-following, photorealistic, supports negative
                 prompts, much closer to Midjourney/DALL-E quality at $0 cost

HOW TO UPGRADE TO FAL.AI (Studio Grade, Image-to-Image):
    See: docs/FAL_AI_UPGRADE.md
    The fal.ai client is at: bot/image_client_fal.py (drop-in replacement)
    Cost: $25 free credit (~500 images) then ~$0.05/image
    Quality: Equivalent to professional ad agency output
"""
import random, time, requests
from typing import Optional, Tuple, Union
from urllib.parse import quote

from config import POLLINATIONS_BASE, POLLINATIONS_PARAMS, HF_API_KEY, HF_MODEL_URL


# ── Type alias ────────────────────────────────────────────────────────────────
# prompt can be a dict {"positive": ..., "negative": ...} OR a plain str
# (str kept for backward compatibility only)
PromptInput = Union[dict, str]


def generate_image(prompt: PromptInput) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Generate an advertising image.

    Args:
        prompt: Either a dict with "positive"/"negative" keys (new format)
                or a plain string (legacy format, still supported).

    Returns:
        (url, None)   — Pollinations succeeded, send this URL to Telegram
        (None, bytes) — Pollinations failed, HF fallback succeeded, send bytes
        (None, None)  — Both failed — caller shows Canva link instead
    """
    positive, negative = _unpack_prompt(prompt)
    seed = random.randint(1, 99999)

    url = _pollinations_flux(positive, negative, seed)
    if url:
        return url, None

    # HuggingFace fallback (only active if HF_API_KEY set in .env)
    data = _huggingface(positive)
    if data:
        return None, data

    # Second HF attempt with quality boosters
    data = _huggingface(positive + ", ultra detailed, photorealistic, 8K")
    return None, data  # may still be None — caller handles gracefully


# ── Internal helpers ──────────────────────────────────────────────────────────

def _unpack_prompt(prompt: PromptInput) -> Tuple[str, str]:
    """
    Normalise prompt input.
    New format: {"positive": "...", "negative": "..."} → returns both
    Old format: "plain string"  → returns (string, generic negative)
    """
    if isinstance(prompt, dict):
        positive = prompt.get("positive", "")
        negative = prompt.get("negative", "text, watermark, logo, blurry, low quality")
    else:
        # Legacy string prompt — wrap it
        positive = str(prompt)
        negative = "text, watermark, logo, blurry, low quality, distorted, pixelated"

    return positive, negative


def _pollinations_flux(positive: str, negative: str, seed: int) -> Optional[str]:
    """
    Call Pollinations.ai with the FLUX model.

    FLUX vs old default model:
      - Much better at following complex, detailed prompts
      - Supports negative prompts (blocks bad outputs)
      - Photorealistic commercial photography quality
      - Still completely free, no API key needed

    URL anatomy:
      /prompt/{positive_prompt}
        ?model=flux         ← key change: FLUX model
        &width=1024         ← HD resolution
        &height=1024
        &nologo=true        ← removes Pollinations watermark
        &enhance=true       ← auto quality boost
        &seed={N}           ← reproducible result
        &negative={negatives} ← blocks unwanted content
    """
    url = (
        POLLINATIONS_BASE.format(prompt=quote(positive))
        + "?"
        + POLLINATIONS_PARAMS.format(seed=seed, negative=quote(negative))
    )
    try:
        r = requests.get(url, timeout=30, stream=True)
        r.raise_for_status()
        if "image" in r.headers.get("content-type", ""):
            return url    # return the URL so Telegram fetches it itself
    except Exception:
        pass
    return None


def _huggingface(prompt: str) -> Optional[bytes]:
    """
    HuggingFace SDXL-Turbo fallback.

    Only runs if HF_API_KEY is set in .env.
    Speed: ~10-20s (can be slower if model is cold/loading).
    Quality: Good, but lower than Pollinations FLUX for this use case.

    To enable: add HF_API_KEY=hf_xxxx to your .env file
    Get a free key at: https://huggingface.co/settings/tokens
    """
    if not HF_API_KEY:
        return None
    try:
        r = requests.post(
            HF_MODEL_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 4,  # SDXL-Turbo is optimised for 4 steps
                    "guidance_scale": 0.0,     # Turbo-specific: 0.0 = distilled model
                }
            },
            timeout=90,
        )
        if r.status_code == 503:
            # Model is loading (cold start) — wait and retry once
            time.sleep(20)
            r = requests.post(
                HF_MODEL_URL,
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                json={"inputs": prompt},
                timeout=90,
            )
        return r.content if r.status_code == 200 else None
    except Exception:
        return None
