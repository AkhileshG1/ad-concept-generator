"""
bot/gemini_client.py — Wrapper around Google Gemini API.

Single multimodal call handles both text generation and photo analysis,
saving quota vs two separate calls.
"""
import json
import re
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL


def _get_model():
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


def generate_ad_copy(prompt: str, photo_bytes_list: list[bytes] | None = None) -> dict:
    """
    Call Gemini with the ad-copy prompt + optional product photos.
    Returns a parsed dict from the JSON response.

    Raises ValueError if JSON cannot be parsed.
    """
    model = _get_model()

    contents = [prompt]

    # Attach photos (if any) — Gemini reads them as visual context
    if photo_bytes_list:
        for photo_bytes in photo_bytes_list[:3]:   # max 3 photos
            contents.append({
                "mime_type": "image/jpeg",
                "data": photo_bytes,
            })

    try:
        result = model.generate_content(
            contents,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.85,          # slightly creative but not wild
                max_output_tokens=2048,
            ),
        )
        raw = result.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e

    # Parse JSON — strip markdown fences if model wraps it anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw[:500]}") from e
