# AdBot — Conversational AI Ad Generator

A chat-based advertising engine that turns a product photo and a description into a professional ad — on Telegram and WhatsApp — in under 3 seconds.

No design skills needed. No subscription required. Just send a message.

---

## What it does

You tell the bot what you're selling. You can send a photo. The bot handles everything else:

- Reads your product photo using Google's Gemini vision model
- Writes ad copy tailored to your business type and platform
- Removes the product background locally (no cloud upload)
- Composes a professional ad using one of four templates
- Delivers the finished image directly inside the chat

The output is sized correctly for Instagram (1080×1080), WhatsApp status (800×800), or a print poster (1080×1350).

It supports 10 languages out of the box — including Arabic with proper right-to-left rendering, Hindi, Chinese, Japanese, and Korean.

Total running cost: $0/month.

---

## Why I built this

Most AI advertising tools cost $30–$150/month and assume you have a laptop, a browser, and a credit card. They're built for marketing teams in English-speaking markets.

But a huge chunk of the world's small business owners run their entire business through WhatsApp. They don't have a Canva subscription. They need an ad for tomorrow's post and they need it fast.

The idea was simple: what if making a professional ad was as easy as sending a WhatsApp message?

This project is my attempt at answering that question.

---

## Honest limitations

I want to be upfront about where this falls short, because I think it matters.

**Image generation quality** — The free FLUX model via Pollinations.ai works well most of the time, but it's not consistent enough for professional advertising at scale. My workaround is a deterministic compositor: instead of generating a background with AI, it removes the product background and composites it onto a professional gradient template. Less creative, but 100% consistent. I wrote a separate post about why this is the hardest unsolved problem in the project.

**Rate limits** — Gemini's free tier has limits. The bot includes retry logic for rate limit errors, but if you're running a high-traffic instance you'll need to think about API costs.

**In-memory sessions** — User state is stored in memory, which means it resets on bot restart. Fine for solo use or demos; not suitable for production without adding a proper database layer.

---

## Stack

| Component | Tool | Why |
|---|---|---|
| AI copy + vision | Gemini 1.5 Pro (free tier) | Best free multimodal model available |
| Background removal | rembg + ONNX | Runs locally, no API cost, no data upload |
| Image fallback | Pollinations.ai FLUX | Free, no key needed, globally accessible |
| Bot framework | python-telegram-bot 21.5 | Mature, async, well-documented |
| Image composition | Pillow | Full control over rendering pipeline |
| Multilingual text | arabic-reshaper + python-bidi | Correct Arabic shaping and RTL layout |

---

## Getting started

### Prerequisites

- Python 3.9 or higher
- A Telegram bot token (free from [@BotFather](https://t.me/BotFather))
- A Gemini API key (free from [Google AI Studio](https://aistudio.google.com/app/apikey))

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/AdBot-Telegram.git
cd AdBot-Telegram

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your environment variables
cp .env.example .env
# Edit .env and add your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY

# Run the bot
python telegram_bot.py
```

You should see:
```
2026-xx-xx | INFO | 🤖 AdBot is live — Ctrl+C to stop
```

Then open Telegram and send `/start` to your bot.

### Required environment variables

```env
TELEGRAM_BOT_TOKEN=   # From @BotFather
GEMINI_API_KEY=        # From aistudio.google.com (free)
```

Optional (leave blank to skip):
```env
HF_API_KEY=            # HuggingFace — image generation fallback
CANVA_AFFILIATE_TAG=   # Canva affiliate ID for passive income
```

---

## How the pipeline works

```
User sends photo + message
        │
        ▼
Gemini 1.5 Pro
  - Reads the product image
  - Identifies product type, color, style
  - Generates headline, body copy, CTA, hashtags
  - Output: structured JSON
        │
        ▼
Background removal (rembg + ONNX — runs locally)
  - Removes background from product photo
  - Returns RGBA image with transparent background
        │
        ▼
Compositor
  - Selects template based on business type
    (Hero Center / Split Screen / Minimalist / Bold Poster)
  - Applies professional gradient background
  - Composites product onto background
  - Renders multilingual typography with correct shaping
  - Outputs platform-correct dimensions
        │
        ▼
Delivered back inside Telegram/WhatsApp chat
```

---

## Bot commands

| Command | What it does |
|---|---|
| `/start` | Begin a new ad — choose business type and platform |
| `/history` | See your last 5 generated ads |
| `/upgrade` | View PRO plans (Telegram Stars) |
| `/status` | Check your current plan and daily usage |
| `/help` | Quick reference |

---

## Ad templates

**Hero Center** — Product centered, headline above, CTA below. Works for most product types.

**Split Screen** — Product on the left, copy on the right. Good for fashion and lifestyle.

**Minimalist** — Clean white-space design, product prominently featured. Good for tech and premium products.

**Bold Poster** — High-contrast, large typography, bullet points. Good for promotions and food.

---

## Supported languages

English, Hindi, Arabic (RTL), French, Spanish, German, Portuguese, Chinese (Simplified), Japanese, Korean.

Arabic was the most complex to implement — it requires character shaping (`arabic-reshaper`) and bidirectional text rendering (`python-bidi`) on top of standard font loading. The layout direction of the entire compositor flips for RTL languages.

---

## Project structure

```
AdBot-Telegram/
│
├── telegram_bot.py          ← Entry point
├── config.py                ← Settings, limits, API URLs
├── requirements.txt
├── .env.example             ← Copy this to .env
│
├── bot/
│   ├── session.py           ← User state and rate limiting
│   ├── prompts.py           ← Prompt engineering (the core logic)
│   ├── gemini_client.py     ← Gemini API wrapper
│   ├── image_client.py      ← Pollinations.ai FLUX
│   ├── bg_remover.py        ← Background removal pipeline
│   ├── compositor.py        ← Template selection and rendering
│   ├── font_manager.py      ← Multilingual font loading
│   ├── language.py          ← Language detection
│   ├── monetization.py      ← Telegram Stars payments
│   ├── links.py             ← WhatsApp + Canva link builders
│   │
│   ├── handlers/            ← Telegram message/callback handlers
│   │   ├── start.py         ← /start flow
│   │   ├── collect.py       ← Product info collection
│   │   ├── generate.py      ← Gemini generation + rating
│   │   ├── image.py         ← Image generation
│   │   ├── deliver.py       ← Ad pack delivery
│   │   └── history.py       ← /history command
│   │
│   └── templates/           ← Compositor templates
│       ├── hero_center.py
│       ├── split_screen.py
│       ├── minimalist.py
│       ├── bold_poster.py
│       ├── _effects.py      ← Shared visual effects
│       └── _utils.py        ← Safe copy field getters
│
├── tests/
│   └── test_v2_full.py      ← 175-test QA suite
│
└── docs/
    ├── ARCHITECTURE.md
    ├── CODE_WALKTHROUGH.md
    └── IMAGE_PIPELINE.md
```

---

## Running the tests

```bash
python -W ignore tests/test_v2_full.py
```

175 tests covering: module imports, language detection, font loading, session management, prompt building, background removal, compositor selection, template rendering, edge cases, multilingual rendering, full pipeline, resilience, performance benchmarks, config validation, and v1 regression.

---

## Freemium model

Free users get 3 ads/day and 2 images/day, with Instagram and WhatsApp output formats.

PRO users (paid via Telegram Stars) get unlimited ads, 10 images/day, and access to Google Ad copy and print poster formats.

Telegram Stars are purchased through Telegram's built-in payment system. There's no external payment processor to set up.

---

## Contributing

Issues and pull requests are welcome. If you're thinking of a larger change, open an issue first to discuss it — saves everyone time.

A few areas where contributions would be genuinely useful:

- **WhatsApp Business API adapter** — The pipeline is platform-agnostic; connecting it to the WhatsApp Cloud API is the main missing piece
- **Persistent session storage** — SQLite or Redis backend for user sessions
- **Better generative backgrounds** — Replacing the deterministic compositor with a more creative approach while keeping consistency
- **New templates** — The compositor accepts new templates cleanly; adding one is a self-contained task

---

## License

MIT. Use it, fork it, build on it. If you build something interesting, I'd genuinely like to see it.
