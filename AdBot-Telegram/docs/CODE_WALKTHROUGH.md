# 🗂️ AdBot-Telegram — Code Walkthrough (Every File Explained)

> This document explains what EVERY file does, why it exists, and how it connects to the others.
> Read this top-to-bottom once and you'll understand the entire codebase.

---

## `telegram_bot.py` — Entry Point

**What it does**: The main file. Starts the bot, registers all command/message handlers.

**Key concept — Handler Registration:**
```python
app.add_handler(CommandHandler("start", cmd_start))
```
This tells Telegram: "When user types /start → call cmd_start function."

**Handler order matters**: Telegram checks handlers top-to-bottom. More specific patterns first.

```python
# Specific callback patterns registered BEFORE generic handlers
app.add_handler(CallbackQueryHandler(handle_photo_option, pattern=r"^photo:(yes|no)$"))
app.add_handler(CallbackQueryHandler(handle_photo_done,   pattern=r"^photo:done$"))

# Generic text handler is LAST (catches everything not matched above)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
```

**Why `drop_pending_updates=True`?**
If the bot was offline and users sent messages, those queue up. We drop them on startup
so users get a fresh experience instead of processing stale messages.

---

## `config.py` — Central Configuration

**What it does**: ALL settings in one place. No magic numbers anywhere else in code.

**Key sections:**

```python
GEMINI_MODEL = "gemini-2.5-flash"   # The AI model for copy generation
```
Only change this ONE line to switch AI models across the entire bot.

```python
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}"
POLLINATIONS_PARAMS = "model=flux&width=1024&height=1024&nologo=true&enhance=true&seed={seed}&negative={negative}"
```
The FLUX model upgrade is here. `model=flux` is what gives us dramatically better images.

```python
class State:
    IDLE            = "idle"
    CHOOSE_BUSINESS = "choose_business"
    # ... etc
```
The State class is a **state machine**. Every user is always in exactly one state.
The state determines what the bot does when the user sends a message.

```python
FREE_ADS_PER_DAY    = 3
FREE_IMAGES_PER_DAY = 2
STARS_WEEKLY  = 50
STARS_MONTHLY = 150
```
Change these numbers to change your pricing and limits — no other code changes needed.

---

## `bot/session.py` — User Session Management

**What it does**: Stores the "conversation state" for every user. Like a shopping cart.

**Why it's needed**: Telegram has no built-in memory. When a user sends "Nike Shoes",
the bot needs to know: are they answering "what's your product?" or typing something random?
The session tracks WHERE in the conversation each user is.

**UserSession class — key fields:**
```python
self.state = State.IDLE          # Where in the flow is the user?
self.business_type = ""          # "food", "fashion", "tech", "services", "other"
self.platform = ""               # "instagram", "whatsapp", "google", "poster", "all"
self.product_name = ""           # "Nike Air Max 90"
self.usp = ""                    # "Lightest running shoe, 30% more cushion"
self.audience = ""               # "Fitness enthusiasts aged 18-35"
self.photos = []                 # List of bytes — uploaded product photos
self.current_copy = {}           # Last generated ad copy dict
self.is_pro = False              # PRO subscription status
self.pro_expires = 0.0           # Unix timestamp when PRO expires
self.ads_today = 0               # Rate limiting counter
```

**SessionManager — key methods:**
```python
sessions.get(user_id)   # Get or create a session (thread-safe with Lock)
```
Uses a `threading.Lock()` because multiple users talk to the bot simultaneously.
Without the lock, two users' data could get mixed up (race condition).

**TTL Eviction:**
```python
SESSION_TTL_SECONDS = 3600  # 1 hour
def _evict_expired(self):
    # Clears sessions for inactive users (except PRO users)
    # Keeps memory usage bounded
```

**Why not use a database?**
For a free-tier bot with <500 users/day, in-memory is faster, simpler, and $0 cost.
The only downside: sessions are lost if bot restarts. See docs/FAL_AI_UPGRADE.md
for how to add Redis persistence when you're ready.

---

## `bot/prompts.py` — The Brain ⭐

**What it does**: All prompt engineering. This is the most important file in the project.

**Why prompt engineering matters so much:**
Gemini is capable of generating garbage OR brilliant copy — the difference is entirely
in how you write the prompt. This file has 3 years of advertising and AI expertise baked in.

### `FEW_SHOT_EXAMPLES` dict
```python
FEW_SHOT_EXAMPLES = {
    "food": "EXAMPLE 1 — Cold Brew: ...",
    "fashion": "EXAMPLE 1 — Sarees: ...",
    ...
}
```
**What it does**: Shows Gemini what GOOD ads look like before asking it to generate one.
This technique is called "few-shot prompting." Without examples, Gemini generates generic copy.
With examples, it understands the tone, structure, and quality bar we expect.

### `COPY_SCHEMA` — JSON contract
```python
COPY_SCHEMA = """
Return ONLY valid JSON. Schema:
{
  "headline": "...",
  "body": "...",
  "cta": "...",
  "hashtags": [...],
  "visual_style": {         ← KEY: This is the Vision DNA output
    "subject": "...",       ← Exact product description from photo analysis
    "composition": "...",   ← How to frame the shot
    "lighting": "...",      ← Lighting setup
    "background": "...",    ← Background description
    "mood": "...",          ← Emotional tone
    "negative": "..."       ← What to block in image generation
  },
  "instagram": {...},
  "whatsapp": {...},
  "google": {...},
  "poster": {...}
}
"""
```
By specifying the exact JSON schema, we force Gemini to return structured data we can parse.
Previously `visual_style` was a plain string (often empty). Now it's a rich object.

### `build_copy_prompt()` — the photo analysis instruction
```python
if session.photos:
    photo_section = """
PRODUCT PHOTO ANALYSIS — REQUIRED:
You have been provided with product photo(s). Examine them carefully.
For visual_style.subject, describe EXACTLY what you see:
  • Precise colors (say "matte army green" not just "green")
  • Materials and textures (leather, mesh fabric, brushed metal, etc.)
  ...
"""
```
**This is Stage 1 of the Vision DNA pipeline.**
Gemini Vision CAN actually see the product photo. This instruction tells it to
extract the product's visual DNA into the `visual_style.subject` field.
That description then gets fed to Pollinations FLUX as the image prompt.

### `build_image_prompt()` — Stable Diffusion prompt engineering
```python
def build_image_prompt(session) -> dict:
    # Returns {"positive": "...", "negative": "..."}
```
**This is Stage 2 of the Vision DNA pipeline.**

Priority chain for each component:
```
Gemini's vision extraction → smart business-type default → generic fallback
```

Professional SD prompt format (this is how Midjourney/FLUX users get great images):
```
{subject}, {composition}, {lighting}, {background}, {mood},
professional advertising photography, commercial quality, 8K ultra sharp focus,
no text, no watermark, no logo overlay
```

The NEGATIVE prompt blocks common failure modes:
```
text, watermark, logo, blurry, low quality, bad anatomy...
```
Food ads block: rotten, unappetizing, human hands
Fashion ads block: bad anatomy, deformed limbs, wrong proportions
Tech ads block: scratched, dirty, broken

---

## `bot/gemini_client.py` — Gemini API Wrapper

**What it does**: One function. Sends prompt (+ optional photos) to Gemini, returns parsed JSON.

```python
def generate_ad_copy(prompt: str, photos: Optional[List[bytes]] = None) -> dict:
    contents = [prompt]
    if photos:
        for p in photos[:3]:  # max 3 photos
            contents.append({"mime_type": "image/jpeg", "data": p})
    result = model.generate_content(contents, ...)
    return json.loads(result.text)
```

**Why `run_in_executor`?** (in generate.py)
Gemini API call is synchronous (blocking) but Telegram bot is async.
If we call Gemini directly, the bot freezes for all other users during generation.
`loop.run_in_executor(None, generate_ad_copy, prompt, photos)` runs the blocking call
in a thread pool, keeping the bot responsive.

**Why `response_mime_type="application/json"`?**
Forces Gemini to return valid JSON, not markdown-wrapped JSON.
Even with this, we strip ```` ```json ``` ```` markers as a safety net.

---

## `bot/image_client.py` — Pollinations FLUX Wrapper

**What it does**: Generates the ad poster image. Now uses FLUX model with neg prompts.

**The key upgrade:**
```python
# OLD (bad):
url = f"https://image.pollinations.ai/prompt/{quote(plain_string)}?width=1024..."

# NEW (good):
url = (
    POLLINATIONS_BASE.format(prompt=quote(positive))
    + "?"
    + POLLINATIONS_PARAMS.format(seed=seed, negative=quote(negative))
)
# POLLINATIONS_PARAMS includes: model=flux&...&negative={negative}
```

**Why FLUX model?**
FLUX (Black Forest Labs) is significantly better than SDXL at:
- Following complex, detailed text prompts
- Maintaining product-specific colors and shapes
- Photorealistic commercial photography style
- Consistent results (less hallucination)

**The `stream=True` trick:**
```python
r = requests.get(url, timeout=30, stream=True)
```
With stream=True, we only download the response headers to check `content-type`.
We return the URL to Telegram, and Telegram fetches the full image itself.
This saves bandwidth (we never download the full image bytes).

---

## `bot/monetization.py` — Telegram Stars Payments

**What it does**: Handles the complete payment flow for PRO subscriptions.

**Flow:**
```
1. User clicks "⭐ Upgrade"
   ↓
2. handle_buy_callback() → context.bot.send_invoice()
   (sends a native Telegram payment request)
   ↓
3. User confirms payment in Telegram app (uses their Stars balance)
   ↓
4. handle_pre_checkout() → always approve (Telegram requirement)
   ↓
5. handle_successful_payment() → session.activate_pro(days)
```

**Critical lines:**
```python
provider_token = ""    # Empty string = Telegram Stars (NOT card payments)
currency = "XTR"       # XTR is the internal code for Telegram Stars
```

**Stars → Cash flow:**
BotFather settings → Fragment.com → convert to TON cryptocurrency → sell on exchange

---

## `bot/handlers/start.py` — Onboarding Flow

**What it does**: Manages `/start` and the business type + platform selection.

**PRO-aware platform selector:**
```python
if session.is_pro:
    rows = [[InlineKeyboardButton(l, ...)] for l,v in ALL_PLATFORMS.items()]
else:
    rows = (
        # Free platforms - clickable
        [[InlineKeyboardButton(l, ...)] for l,v in PLATFORMS_FREE.items()]
        +
        # PRO platforms - shown but locked (greyed text + lock icon)
        [[InlineKeyboardButton(f"🔒 {l} — PRO only", callback_data="platform:upgrade")]
         for l,v in PLATFORMS_PRO.items()]
    )
```
Free users SEE the PRO options (creates desire) but can't click them.
This is a classic freemium conversion technique.

---

## `bot/handlers/collect.py` — Data Collection

**What it does**: The sequential form-filling step. Collects 3 text inputs + optional photos.

**State machine routing:**
```python
async def handle_text(update, context):
    session = sessions.get(update.effective_user.id)
    text = update.message.text.strip()

    if session.state == State.GET_PRODUCT:
        session.product_name = text
        session.state = State.GET_USP   # advance to next state
        await update.message.reply_text("What makes it special?...")

    elif session.state == State.GET_USP:
        session.usp = text
        session.state = State.GET_AUDIENCE
        ...

    elif session.state == State.AWAITING_RATING:
        # User typed feedback text after rating 1-3
        await regenerate_with_feedback(update, context, text)
```
One function handles ALL text messages. The current state determines what to do.

---

## `bot/handlers/generate.py` — AI Generation + Rating

**What it does**: Calls Gemini, displays the copy, handles the rating feedback loop.

**Async executor pattern (critical for performance):**
```python
# WRONG (freezes bot for all users):
copy = generate_ad_copy(prompt, photos)

# RIGHT (runs in thread, bot stays responsive):
loop = asyncio.get_running_loop()
copy = await loop.run_in_executor(None, generate_ad_copy, prompt, photos)
```

**Rating logic:**
- Rate 4-5 or click "Approve" → proceed to image generation
- Rate 1-3 → show "What should change?" prompt
- After 3 low ratings → fall through anyway (prevent infinite loops)

---

## `bot/handlers/image.py` — Image Generation

**What it does**: Builds the image prompt, calls Pollinations FLUX, delivers result.

```python
img_prompt = build_image_prompt(session)  # Returns dict {positive, negative}

loop = asyncio.get_running_loop()
url, img_bytes = await loop.run_in_executor(None, generate_image, img_prompt)
```

**Image limit enforcement:**
```python
if not session.can_generate_image():
    # Show limit message
    await deliver_copy_only(...)  # Give copy at least, no image
    return
```
Free users can only generate 2 images/day. This protects Pollinations quota.

---

## `bot/handlers/deliver.py` — Ad Pack Delivery

**What it does**: Formats and sends the complete ad pack to the user.

**Chunked sending:**
```python
async def _send_long(message, text, **kw):
    for chunk in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await message.reply_text(chunk, **kw)
```
Telegram's max message length is 4096 chars. Long ad packs get split automatically.

**Canva affiliate tagging:**
```python
canva_url = get_canva(session.business_type, session.platform)
# This returns: "https://canva.com/templates/?query=food+instagram&referrer=YOUR_TAG"
# If user signs up for Canva Pro → you earn commission
```

---

## `bot/links.py` — Link Builders

**What it does**: Platform-specific text formatters and affiliate link builders.

Key functions:
- `instagram_caption(copy)` → formats copy for Instagram character/style standards
- `whatsapp_text(copy)` → conversational format for WhatsApp
- `google_ad_block(copy)` → H1/H2/H3/D1/D2 Google Ads format
- `whatsapp_link(text)` → creates `wa.me/?text=...` pre-filled share link
- `get_canva(btype, platform)` → returns the matching Canva template URL

---

## `bot/quality.py` — Copy Validator

**What it does**: Simple rule-based checks on the generated copy.

Checks:
- Is the headline too long for the platform?
- Does the CTA contain forbidden phrases like "Buy Now" or "Click Here"?
- Are there too few/many hashtags?

Returns a warning string shown to the user below the copy.

---

## Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---|---|---|
| `python-telegram-bot` | 21.5 | Telegram API client (async, v20+ API) |
| `google-generativeai` | 0.7.2 | Gemini Vision + text generation |
| `python-dotenv` | 1.0.1 | Load .env file into environment |
| `requests` | 2.32.3 | HTTP calls to Pollinations.ai |
| `Pillow` | 10.4.0 | Image processing (if needed) |

**Future (fal.ai upgrade):**
```
fal-client==0.5.0   # Add when activating bot/image_client_fal.py
```
