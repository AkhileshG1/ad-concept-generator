"""
bot/gemini_client.py — Single multimodal Gemini call for both copy + vision.

JSON PARSING — WHY IT'S ROBUST NOW:
    Gemini 2.5 Flash (thinking model) can output:
      - <think>...</think> tokens before the actual JSON
      - ```json ... ``` markdown code fences
      - Extra explanatory text before/after the JSON object
      - Partial JSON if max_output_tokens is hit

    We handle all of these with a 3-stage parse chain:
    1. Strip thinking tokens + try direct parse
    2. Strip markdown fences + try parse
    3. Regex-find the largest {...} block + try parse
    4. Raise a clear error with the raw text for debugging
"""
import json
import re
import logging
from typing import List, Optional

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

log = logging.getLogger(__name__)


def generate_ad_copy(prompt: str, photos: Optional[List[bytes]] = None) -> dict:
    """
    Call Gemini with a prompt (+ optional product photos) and return parsed JSON.

    The response_mime_type="application/json" hint tells Gemini to output JSON,
    but Gemini 2.5 Flash (thinking model) still prefixes with thinking tokens.
    _safe_json_parse() handles all of this gracefully.

    Args:
        prompt: The full copy-generation prompt (from build_copy_prompt)
        photos: Optional list of raw image bytes (from session.photos)

    Returns:
        Parsed dict with headline, body, cta, visual_style etc.

    Raises:
        ValueError: If JSON cannot be extracted after all fallback attempts
        Any Gemini API error (quota, auth, model unavailable)
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Build the multimodal content list
    # Text prompt first, then photo bytes (Gemini Vision)
    contents = [prompt]
    if photos:
        for p in photos[:3]:  # max 3 photos
            contents.append({"mime_type": "image/jpeg", "data": p})

    result = model.generate_content(
        contents,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",  # Hint: return JSON
            temperature=0.85,                       # Creative but consistent
            max_output_tokens=4096,                 # Increased: rich visual_style needs more tokens
        ),
    )

    return _safe_json_parse(result.text)


def _safe_json_parse(raw_text: str) -> dict:
    """
    Robustly extract and parse JSON from Gemini's raw output.

    Handles all the ways Gemini 2.5 Flash can "wrap" its JSON:
      - <think>chain of thought</think> prefix (thinking model)
      - ```json ... ``` markdown fences
      - Plain text explanation before/after the JSON
      - Extra whitespace or unicode characters

    Parse chain (stops at first success):
      Stage 1 → strip <think> tags, try direct parse
      Stage 2 → strip markdown fences, try parse
      Stage 3 → regex-find the outermost {...}, try parse
      Stage 4 → raise ValueError with snippet for debugging
    """
    text = raw_text.strip()

    # ── Stage 1: Strip thinking tokens (Gemini 2.5 Flash thinking mode) ──────
    # Gemini 2.5 Flash outputs <think>...</think> before the actual answer.
    # This is the most common cause of JSONDecodeError on 2.5 models.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # ── Stage 2: Strip markdown code fences ───────────────────────────────────
    # Gemini sometimes wraps output in ```json ... ``` even with response_mime_type set
    text2 = re.sub(r"^```(?:json)?\s*", "", text)
    text2 = re.sub(r"\s*```$", "", text2).strip()
    try:
        return json.loads(text2)
    except json.JSONDecodeError:
        pass

    # ── Stage 3: Find outermost JSON object via regex ─────────────────────────
    # If there's any text before/after the JSON object, this extracts just the JSON.
    # Uses re.DOTALL so {...} can span multiple lines.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # ── Stage 4: Give up with a useful debug message ──────────────────────────
    snippet = raw_text[:300].replace("\n", " ")
    log.error(f"JSON parse failed. Raw Gemini output (first 300 chars): {snippet}")
    raise ValueError(
        f"Gemini returned non-JSON output. "
        f"First 200 chars: {raw_text[:200]!r}"
    )
