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
import time
import logging
from typing import List, Optional

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

log = logging.getLogger(__name__)

# ── Retry config for rate limits ──────────────────────────────────────────────
MAX_RETRIES = 3
BASE_DELAY = 10  # seconds — free tier resets in ~8-10s


def generate_ad_copy(prompt: str, photos: Optional[List[bytes]] = None) -> dict:
    """
    Call Gemini with a prompt (+ optional product photos) and return parsed JSON.

    Includes automatic retry with exponential backoff for 429 rate limit errors.
    Free tier allows 5 requests/minute — retries silently wait and try again.

    Args:
        prompt: The full copy-generation prompt (from build_copy_prompt)
        photos: Optional list of raw image bytes (from session.photos)

    Returns:
        Parsed dict with headline, body, cta, visual_style etc.

    Raises:
        ValueError: If JSON cannot be extracted after all fallback attempts
        Exception: If all retries exhausted or non-retryable error
    """
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)

    # Build the multimodal content list
    # Text prompt first, then photo bytes (Gemini Vision)
    contents = [prompt]
    if photos:
        for p in photos[:3]:  # max 3 photos
            contents.append({"mime_type": "image/jpeg", "data": p})

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = model.generate_content(
                contents,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                    max_output_tokens=4096,
                ),
            )
            return _safe_json_parse(result.text)

        except Exception as e:
            last_error = e
            error_str = str(e)

            # Only retry on 429 rate limit errors
            if "429" not in error_str and "quota" not in error_str.lower():
                raise  # Non-retryable error — raise immediately

            if attempt < MAX_RETRIES:
                # Extract retry delay from error if available, or use backoff
                delay = _extract_retry_delay(error_str) or (BASE_DELAY * (2 ** attempt))
                log.warning(
                    f"Rate limited (attempt {attempt + 1}/{MAX_RETRIES + 1}). "
                    f"Waiting {delay:.0f}s before retry..."
                )
                time.sleep(delay)
            else:
                log.error(f"All {MAX_RETRIES + 1} attempts exhausted. Last error: {e}")

    raise last_error


def _extract_retry_delay(error_str: str) -> Optional[float]:
    """Extract the retry delay from a Gemini 429 error message."""
    # Pattern: "retry in 8.593970094s" or "seconds: 8"
    match = re.search(r"retry[_ ]?(?:in|delay)[:\s]*(\d+\.?\d*)", error_str, re.IGNORECASE)
    if match:
        return float(match.group(1)) + 1.0  # Add 1s buffer

    match = re.search(r"seconds:\s*(\d+)", error_str)
    if match:
        return float(match.group(1)) + 1.0

    return None


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
