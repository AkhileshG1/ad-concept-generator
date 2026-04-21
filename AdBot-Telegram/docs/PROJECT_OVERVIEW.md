# 🤖 AdBot-Telegram — Complete Project Overview

> **Mission**: A professional AI Marketing Agency, distilled into a Telegram Bot.
> **Cost**: $0/month to run. **Users**: ~500/day on free tiers.

---

## Table of Contents
1. [What This Bot Does](#what-this-bot-does)
2. [Architecture Overview](#architecture-overview)
3. [File Structure](#file-structure)
4. [Full User Journey](#full-user-journey)
5. [Revenue Model](#revenue-model)
6. [How to Run](#how-to-run)
7. [Environment Variables](#environment-variables)

---

## What This Bot Does

AdBot takes a user from **"I have a product"** to **"I have a professional ad"** in under 2 minutes, entirely inside Telegram.

### Output (what the user receives):
```
📸 An AI-generated product poster image
📝 Instagram caption (headline + body + hashtags)
💬 WhatsApp message (conversational format)
🔍 Google Ad copy (character-limited H1/H2/H3/D1/D2)
🖼️  Print Poster text (headline + bullets + CTA)
🔀 A/B headline variation to test
🎨 Canva template link (matched to their industry + platform)
💬 One-click WhatsApp share button
```

---

## Architecture Overview

```
USER (Telegram App)
        │
        ▼  webhooks/polling
TELEGRAM BOT SERVER (telegram_bot.py)
        │
        ├─── bot/handlers/start.py      → Onboarding flow
        ├─── bot/handlers/collect.py    → Product info collection
        ├─── bot/handlers/generate.py   → Triggers AI copy generation
        ├─── bot/handlers/image.py      → Triggers AI image generation
        ├─── bot/handlers/deliver.py    → Formats and sends the ad pack
        ├─── bot/handlers/history.py    → Shows past 5 ads
        │
        ├─── bot/session.py             → User state management (in-memory)
        ├─── bot/prompts.py             → Prompt engineering (THE BRAIN)
        ├─── bot/gemini_client.py       → Gemini API wrapper
        ├─── bot/image_client.py        → Pollinations.ai FLUX wrapper
        ├─── bot/image_client_fal.py    → [REFERENCE] fal.ai upgrade path
        ├─── bot/monetization.py        → Telegram Stars payment flow
        ├─── bot/links.py               → Canva / WhatsApp link builders
        ├─── bot/quality.py             → Copy quality validator
        │
        ├─── config.py                  → All constants, API URLs, tier limits
        └─── .env                       → Secret keys (never commit this!)

EXTERNAL APIs (all free tier):
        ├─── Gemini 2.5 Flash           → AI copy + product photo analysis
        └─── Pollinations.ai FLUX       → Ad poster image generation
```

---

## File Structure

```
AdBot-Telegram/
│
├── telegram_bot.py          ← Entry point. Run this to start the bot.
├── config.py                ← All settings, limits, URL templates
├── requirements.txt         ← Python dependencies
├── .env                     ← YOUR SECRET KEYS (never share/commit)
├── .env.example             ← Template showing what keys are needed
├── bot_logo.png             ← Bot profile picture (set in BotFather)
│
├── bot/
│   ├── __init__.py
│   ├── session.py           ← User session: state machine + rate limits
│   ├── prompts.py           ← ⭐ Core: prompt engineering + image prompt builder
│   ├── gemini_client.py     ← Calls Gemini API, returns structured JSON
│   ├── image_client.py      ← Calls Pollinations.ai FLUX (active)
│   ├── image_client_fal.py  ← [REFERENCE] fal.ai studio-grade (not active)
│   ├── monetization.py      ← Telegram Stars payments + PRO tier logic
│   ├── links.py             ← WhatsApp links + Canva affiliate links
│   ├── quality.py           ← Validates generated copy quality
│   │
│   └── handlers/
│       ├── __init__.py
│       ├── start.py         ← /start command + business/platform selector
│       ├── collect.py       ← Collects product name, USP, audience, photos
│       ├── generate.py      ← Sends to Gemini, shows copy + rating buttons
│       ├── image.py         ← Sends to Pollinations, handles image limits
│       ├── deliver.py       ← Formats complete ad pack, sends to user
│       └── history.py       ← /history command
│
└── docs/
    ├── PROJECT_OVERVIEW.md     ← This file
    ├── CODE_WALKTHROUGH.md     ← Every file explained in depth
    ├── IMAGE_PIPELINE.md       ← How the image quality upgrade works
    └── FAL_AI_UPGRADE.md       ← How to upgrade to studio-grade images
```

---

## Full User Journey

```
/start
  │
  ▼
Choose Business Type
  [🍕 Food] [👗 Fashion] [💻 Tech] [🔧 Services] [🎯 Other]
  │
  ▼
Choose Platform
  [📸 Instagram] [💬 WhatsApp]  ← Free
  [🔒 Google Ad] [🔒 Poster]   ← PRO only
  │
  ▼
"What's your product name?"
  │
  ▼
"What makes it special? (USP)"
  │
  ▼
"Who is your target audience?"
  │
  ▼
"Do you have product photos?"
  [📸 Yes] [⚡ Skip]
  │
  ├── (if Yes) Upload up to 3 photos → Gemini analyzes them (Vision DNA ⭐)
  │
  ▼
Gemini generates ad copy (JSON with all fields)
User sees: Headline, Body, CTA, Hashtags, A/B variation, Audience note
  │
  ▼
Rate the ad:  [⭐1] [⭐2] [⭐3] [⭐4] [⭐5] [✅ Looks great!]
  │
  ├── (Rated 1-3) → "What should change?" → Gemini regenerates with feedback
  └── (Rated 4-5 or Approved) → Generate poster image
  │
  ▼
Pollinations.ai FLUX generates poster
  │
  ▼
Deliver Complete Ad Pack:
  📸 Image + Instagram caption
  💬 WhatsApp message
  🔍 Google Ad (PRO)
  🖼️ Poster text (PRO)
  🔀 A/B headline
  🎨 Canva template link (affiliate tagged)
  💬 WhatsApp share button
  [🔁 Make Another Ad] [📚 My History] [⭐ Upgrade]
```

---

## Revenue Model

### Stream 1: Telegram Stars (Primary)
| Plan | Stars | USD equiv | Duration |
|---|---|---|---|
| Weekly | 50 ⭐ | ~$0.65 | 7 days |
| Monthly | 150 ⭐ | ~$1.95 | 30 days |
| Quarterly | 500 ⭐ | ~$6.50 | 90 days |

Stars are collected inside Telegram. Withdraw via:
`BotFather → Fragment → TON → sell for cash`

**PRO unlocks:**
- Unlimited ads (Free: 3/day)
- 10 images/day (Free: 2/day)
- Google Ad copy format
- Print Poster format
- Full Ad Pack (all 4 platforms at once)

### Stream 2: Canva Affiliate (Passive)
- Every ad delivery includes an "Edit on Canva" button
- URL is tagged: `canva.com/templates/?referrer=YOUR_TAG`
- If user signs up for Canva Pro → you earn 25–80% commission
- Zero effort, zero cost, auto-appended to every single ad

**To activate:** Sign up at canva.com/affiliates → add tag to .env

---

## How to Run

```bash
# 1. Navigate to project
cd "/Users/akhilesh/Documents/Add AI agent/AdBot-Telegram"

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start the bot
python telegram_bot.py
```

You should see:
```
2026-xx-xx | INFO | 🤖 AdBot is live — Ctrl+C to stop
```

---

## Environment Variables

File: `.env` (never commit this to git — it contains your secret keys)

```env
# Required
TELEGRAM_BOT_TOKEN=xxxx   # From @BotFather on Telegram
GEMINI_API_KEY=xxxx       # From https://aistudio.google.com/app/apikey

# Optional (leave blank to skip)
HF_API_KEY=               # HuggingFace — for image generation fallback
CANVA_AFFILIATE_TAG=      # Your Canva affiliate ID — passive income
FAL_API_KEY=              # fal.ai — for studio-grade image upgrade
```
