"""
bot/image_client.py — Image generation with automatic fallback chain.

Priority:
  1. Pollinations.ai — No API key, ~5s, free forever
  2. HuggingFace SDXL-Turbo — Needs HF_API_KEY, ~15s

Returns: URL (Pollinations) or bytes (HF fallback).
The caller should check the type to know how to send it to Telegram.
"""
import random
import time
import requests
from urllib.parse import quote

from config import POLLINATIONS_URL, HF_API_KEY, HF_MODEL_URL
from bot.quality import is_image_acceptable


def generate_image(prompt: str) -> tuple[str | None, bytes | None]:
    """
    Returns (url_or_none, bytes_or_none).
    One of the two will be set, the other None.
    Try Pollinations first, then HF fallback.
    """
    seed = random.randint(1, 99999)
    url = _try_pollinations(prompt, seed)
    if url:
        return url, None

    # Fallback to HuggingFace
    img_bytes = _try_huggingface(prompt)
    if img_bytes and is_image_acceptable(img_bytes):
        return None, img_bytes

    # Second HF attempt with tweaked prompt
    tweaked = prompt + ", ultra detailed, photorealistic, award winning"
    img_bytes = _try_huggingface(tweaked)
    if img_bytes:
        return None, img_bytes

    return None, None    # both failed — caller handles gracefully


def _try_pollinations(prompt: str, seed: int) -> str | None:
    """
    Pollinations.ai returns a direct image URL; Telegram can display it inline.
    We verify the URL actually serves an image before returning it.
    """
    encoded = quote(prompt)
    url = POLLINATIONS_URL.format(prompt=encoded, seed=seed)
    try:
        # HEAD check — don't download the whole image just to verify
        r = requests.head(url, timeout=15, allow_redirects=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return url
        # Some CDN configs don't support HEAD, do a ranged GET
        r = requests.get(url, timeout=20, stream=True)
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        if "image" in content_type:
            return url
    except Exception:
        pass
    return None


def _try_huggingface(prompt: str) -> bytes | None:
    """Call HF Inference API and return raw image bytes."""
    if not HF_API_KEY:
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_inference_steps": 4,   # SDXL-Turbo is optimised for 4 steps
            "guidance_scale": 0.0,
            "width": 1024,
            "height": 1024,
        },
    }
    try:
        r = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=60)
        if r.status_code == 200 and r.content:
            return r.content
        if r.status_code == 503:
            # Model loading — wait and retry once
            time.sleep(20)
            r = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=90)
            if r.status_code == 200 and r.content:
                return r.content
    except Exception:
        pass
    return None
