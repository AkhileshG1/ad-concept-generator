# AdBot v2 — Changes Log & Known Issues
> Session date: 2026-04-22 | Author: Antigravity AI (pair programming session)

---

## Table of Contents
1. [Session Summary](#1-session-summary)
2. [Changes Made](#2-changes-made)
3. [Bugs Fixed](#3-bugs-fixed)
4. [Known Issues — Open](#4-known-issues--open)
5. [Gemini Rate Limit — Root Cause & Planned Fix](#5-gemini-rate-limit--root-cause--planned-fix)
6. [Test Results](#6-test-results)

---

## 1. Session Summary

This session covered three major workstreams:

| # | Area | Status |
|---|---|---|
| 1 | QA test run — full suite | ✅ 175/175 passed |
| 2 | Visual compositor overhaul (agency-grade) | ✅ Done |
| 3 | Pipeline architectural fix (Pollinations bypass) | ✅ Done |
| 4 | Multiple bot process cleanup | ✅ Done |
| 5 | Gemini rate limit fix | 🔴 Documented, **not yet implemented** |

---

## 2. Changes Made

### 2.1 `bot/templates/_effects.py` — Full Rewrite

**Problem:** Effects library was basic and missing key agency-grade primitives.

**Changes:**
- Added `add_noise_texture()` — subtle grain for premium print feel
- Added `add_dot_pattern()` — parametric dot grid overlay
- Added `add_scanlines()` — horizontal scanlines for tech/dark aesthetic
- Added `add_vignette()` — dark edge vignette to focus on centre
- Added `add_frosted_glass_panel()` — glassmorphism text panel
- Added `add_product_reflection()` — floor reflection effect (studio look)
- Added `draw_premium_badge()` — pill-shaped badge (NEW, 50% OFF, PRO)
- Added `draw_text_with_shadow()` — proper multiline text shadow compositing
- Added `make_diagonal_gradient()` — diagonal gradient for dynamic feel
- Upgraded `enhance_product()` — now boosts saturation (+25%) and sharpness (+40%)
- Upgraded `add_drop_shadow()` — now renders two shadow layers (outer + inner) for realism
- Upgraded `add_glow_behind()` — two-layer glow (wide soft + tight bright halo)

---

### 2.2 `bot/templates/hero_center.py` — Agency-Grade Overhaul

**Problem:** Output was competent but not premium. Product zone was undersized, no reflection, basic CTA button.

**Changes:**
- Added top accent bar + business type label (small caps)
- Headline now uses `draw_text_with_shadow()` with proper 4px offset + 12px blur
- Multi-layer glow halo (accent colour + white inner halo)
- `add_product_reflection()` — floor reflection below product
- Body text now in **frosted glass panel** (glassmorphism) — no more raw text on gradient
- Body text limit raised from 100 → 140 chars; properly word-wrapped
- CTA button now uses **gradient fill** (lighter top → darker base) via `make_gradient()`
- Hashtag strip added at the very bottom of the canvas

---

### 2.3 `bot/templates/bold_poster.py` — Agency-Grade Overhaul

**Changes:**
- Header band now uses gradient (`header_col → header_bot`) instead of flat colour
- Dot texture added on header band for depth
- Accent stripe (5px) at bottom of header band
- Headline inside header uses `draw_text_with_shadow()`
- Product zone now **dynamically calculates** available height based on bullet count + button space (no more overlap)
- Product now gets accent-coloured glow + white inner halo + drop shadow
- `add_product_reflection()` added below product
- CTA button uses gradient fill + shadow layer
- Updated `VIBRANT_PALETTES` with richer, more differentiated `header_bot` keys

---

### 2.4 `bot/templates/split_screen.py` — Agency-Grade Overhaul

**Changes:**
- Accent stripe between panels is now **angled/diagonal** (slanted polygon, not vertical line)
- Left panel: radial glow overlay centred on product zone
- Product gets 2-layer glow (accent + white inner halo) + drop shadow + floor reflection
- Right panel: category label is now a **pill-shaped badge** (not plain text)
- Headline uses `draw_text_with_shadow()`
- Body text limit raised from 130 → 140 chars
- CTA button uses gradient fill; text uses auto-contrast (dark on light, white on dark)
- Hashtag strip added below CTA button
- `RIGHT_BG` and `TEXT_COLORS` dictionaries added for better per-category right-panel colours

---

### 2.5 `bot/templates/minimalist.py` — Agency-Grade Overhaul

**Changes:**
- Scanline overlay added (`add_scanlines()`)
- Two-layer electric glow (wide + tight) behind product
- Floor reflection added
- Headline + body now inside a **frosted glass panel** (glassmorphism)
- CTA underline is now **3-layer glowing underline** (wide soft → medium → sharp)
- Top accent bar (glow colour) at very top of canvas

---

### 2.6 `bot/templates/scene_overlay.py` — NEW FILE

**Problem (architectural flaw — see §3.1):** The Pollinations pipeline sent raw AI-generated images directly to Telegram without any typography rendering or branding.

**Solution:** New `scene_overlay` template that takes any full-scene image (from Pollinations or other AI sources) and composites professional branding on top:

| Layer | What it does |
|---|---|
| Scene image | Smart centre-cropped to exact platform canvas (1080×1080 / 1080×1350 / 800×800) |
| Top luminous overlay | Accent-coloured gradient (top 30%), fades to transparent |
| Dark gradient | Bottom 55% darkens smoothly for text readability |
| Vignette | Draws attention to centre |
| Accent top bar | Brand colour line at top |
| Headline | Bold white text with 4px/14px shadow, word-wrapped |
| Accent underline | Thin coloured line under headline |
| Body text | Full text up to 200 chars in frosted glass panel |
| CTA button | Gradient pill button, auto-contrast text |
| Hashtag strip | Bottom of canvas |

---

### 2.7 `bot/handlers/image.py` — Pipeline Architecture Fix

**Problem (see §3.1):** `_pollinations_pipeline` bypassed the compositor entirely.

**Changes:**
```
OLD:  Pollinations → raw JPEG URL → Telegram
NEW:  Pollinations → raw JPEG bytes → scene_overlay compositor → branded JPEG → Telegram
```

Full rewrite of `_pollinations_pipeline`:
1. Extracts `copy`, `business_type`, `platform`, `language` from session
2. Calls Pollinations to generate scene image (bytes)
3. Passes bytes through `scene_overlay.compose()` in thread pool executor
4. Delivers the branded JPEG via `deliver_full_pack(img_bytes=...)`
5. Fallback: if `scene_overlay` fails, raw Pollinations image is used (acceptable safety net)

---

### 2.8 Multiple Bot Process Fix

**Problem:** Each bot restart during the session left the previous process running. Three instances were simultaneously polling Telegram, causing message delivery race conditions.

**Fix:** `kill -9 <all PIDs>` to clean state, then single clean restart.

**Future prevention:** Always use this command to restart:
```bash
pkill -f telegram_bot.py && sleep 1 && venv/bin/python telegram_bot.py
```

---

## 3. Bugs Fixed

### 3.1 🔴 [CRITICAL] Pollinations pipeline bypassed compositor

**Symptom:** When no product photo was uploaded, the output was a dark AI-generated background (space/abstract) with only Telegram caption text. No professional typography, no CTA button, no layout.

**Root cause:** `_pollinations_pipeline` called `deliver_full_pack(img_url=url)` which sent the raw Pollinations image URL to Telegram. The compositor was never invoked.

**Fix:** `scene_overlay.py` + rewired pipeline (see §2.6, §2.7).

---

### 3.2 🟡 [MEDIUM] Body text truncated at 100 chars

**Symptom:** Body text visibly cut off mid-sentence (e.g., "...classic court style and modern comfort. Des").

**Root cause:** `body_raw[:100]` in `hero_center.py` and `body_raw[:90]` in `minimalist.py`.

**Fix:** Raised limits → `hero_center`: 140 chars, `minimalist`: 120 chars, `scene_overlay`: 200 chars. All with proper word-wrap so text never overflows the canvas.

---

### 3.3 🟡 [MEDIUM] Minimalist template `list index out of range`

**Symptom:** All 3 minimalist renders failed in the initial agency upgrade pass.

**Root cause:** Glow underline loop used `[80, 160, 255][5 - thickness - 1]` which produces index values of 1, 2, 4 — index 4 is out of range for a 3-element list.

**Fix:** Replaced with explicit `glow_layers = [(5, 60), (3, 130), (1, 220)]` tuple iteration.

---

### 3.4 🟡 [MEDIUM] Three duplicate bot processes

**Symptom:** Bot would respond erratically; some messages handled multiple times or not at all.

**Root cause:** Bot was restarted multiple times without killing previous instances. PIDs 1397, 1741, 1779 all polling simultaneously.

**Fix:** `kill -9` all PIDs + single clean start (see §2.8).

---

## 4. Known Issues — Open

### 4.1 🔴 [CRITICAL] Gemini Free-Tier Rate Limit (429 Too Many Requests)

**Status: NOT YET FIXED — documented here for next session.**

**Symptom:**
```
⏳ AI is busy right now — too many requests per minute.
The bot tried 3 times automatically but the API is still throttled.
Please wait 30 seconds and try again.
💡 This is a free-tier rate limit (5 requests/minute), not a billing issue.
```

**See §5 for full root cause analysis and planned fix.**

---

### 4.2 🟡 [MEDIUM] `scene_overlay` not covered by QA test suite

The existing `test_v2_full.py` tests all 4 original templates but does not test `scene_overlay.py`.

**Planned:** Add a Section 16 to `test_v2_full.py`:
- scene_overlay renders correctly on all 3 platforms
- scene_overlay handles corrupt scene image gracefully
- scene_overlay handles very long body text (200 chars)
- scene_overlay handles missing hashtags

---

### 4.3 🟢 [LOW] Python 3.9 End-of-Life warnings from Google SDK

**Symptom:** On every bot start:
```
FutureWarning: You are using a Python version 3.9 past its end of life.
```

**Impact:** Cosmetic only — bot functions correctly. Google will stop backporting security fixes.

**Fix:** Upgrade to Python 3.11+ and rebuild venv. Low priority.

---

## 5. Gemini Rate Limit — Root Cause & Planned Fix

### 5.1 Root Cause

The Gemini free tier allows **5 requests per minute (RPM)**. The current retry logic in `gemini_client.py`:

```python
MAX_RETRIES = 3
BASE_DELAY  = 10   # seconds

# Retry delays: 10s, 20s, 40s = 70s total blocking time
delay = BASE_DELAY * (2 ** attempt)
time.sleep(delay)
```

**Problems:**
1. `time.sleep()` blocks the thread pool executor — while retrying, Telegram's webhook/polling may time out (30s default), so the user sees the error message before retries finish.
2. There is **no pre-emptive throttle** — the bot fires Gemini requests as fast as users send them. If 2 users generate ads within the same minute, the second request immediately 429s.
3. The error message shown to the user is accurate but unhelpful — it tells them to "wait 30 seconds" but there is no automatic queue.

### 5.2 Planned Fix (for next session)

**Strategy: Token Bucket Rate Limiter + async-safe retries**

#### Step 1 — Add a global token bucket in `gemini_client.py`

```python
import asyncio
import threading
import time

class _TokenBucket:
    """Thread-safe token bucket — allows MAX_RPM calls per 60 seconds."""
    def __init__(self, rate: int = 4):  # Stay under 5 RPM with a 1-request buffer
        self._rate  = rate          # tokens added per minute
        self._tokens = rate         # start full
        self._lock   = threading.Lock()
        self._last   = time.monotonic()

    def acquire(self, timeout: float = 90.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._tokens = min(self._rate, self._tokens + elapsed * (self._rate / 60.0))
                self._last = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return True
            time.sleep(1)
        return False  # Timed out

_bucket = _TokenBucket(rate=4)  # Conservative: 4/min, hard limit is 5/min
```

#### Step 2 — Use bucket in `generate_ad_copy()`

```python
def generate_ad_copy(prompt, photos=None):
    if not _bucket.acquire(timeout=90):
        raise RuntimeError("Rate limit queue timed out after 90s")
    # ... existing Gemini call
```

#### Step 3 — Better retry with jitter

```python
MAX_RETRIES = 5
for attempt in range(MAX_RETRIES):
    try:
        ...
    except Exception as e:
        if "429" in str(e):
            delay = _extract_retry_delay(str(e)) or (12 * (1.5 ** attempt))
            jitter = random.uniform(0, 3)  # Avoid thundering herd
            time.sleep(delay + jitter)
        else:
            raise
```

#### Step 4 — Better UX message while queuing

In `generate.py`, show a "queued" message before calling Gemini:
```python
await message.reply_text("⏳ Queuing your request... (API rate limit: ~1 per 15s)")
copy = await loop.run_in_executor(None, generate_ad_copy, prompt, photos)
```

#### Step 5 — Consider upgrading Gemini tier

The `gemini-2.5-flash` free tier is **5 RPM / 500 RPD**.  
Gemini API **Pay-as-you-go** starts at ~$0.075 per 1M input tokens — for this bot's usage, it would cost **< $1/month** and raises limits to **1000 RPM**.

This is the recommended long-term solution.

---

## 6. Test Results

### Before session (baseline)
| Metric | Value |
|---|---|
| Tests | 175 passed / 0 failed |
| Render speed avg | 0.131s/frame |

### After session (post-overhaul)
| Metric | Value |
|---|---|
| Tests | 175 passed / 0 failed ✅ |
| Render speed avg | 0.315s/frame |
| Render speed max | 0.49s (within 3.0s limit) ✅ |
| File sizes | 82KB–166KB per platform ✅ |
| New templates added | `scene_overlay.py` |
| New effects added | 8 new effect functions |

> **Why is render speed ~2.4× slower?**  
> Each frame now renders more layers: 2-layer glow, floor reflection, frosted glass panel, scanlines, vignette, gradient button. All still under the 3.0s performance limit.

---

*Generated: 2026-04-22 | Next session: Fix Gemini rate limit (§5.2)*
