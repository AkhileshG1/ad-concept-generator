# Contributing to AdBot

Thanks for your interest. Here's how to get started without wasting time.

## Before you open a PR

For small fixes (typos, broken links, minor bugs) — just open a PR directly.

For anything larger — a new template, a new platform adapter, a storage backend — please open an issue first. Not because I want gatekeeping, but because I may already be working on something that overlaps, or I might have context that changes the approach.

## Setting up locally

```bash
git clone https://github.com/yourusername/AdBot-Telegram.git
cd AdBot-Telegram

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add your TELEGRAM_BOT_TOKEN and GEMINI_API_KEY to .env
```

## Running tests

```bash
python -W ignore tests/test_v2_full.py
```

All 175 tests should pass before you submit a PR. If you're adding new functionality, add tests for it in the same file — it's a single flat test suite by design.

## Areas where help is most useful

**WhatsApp Business API adapter**
The pipeline is fully platform-agnostic. The Telegram bot is just an adapter layer on top of it. Connecting the same pipeline to the WhatsApp Cloud API would make this usable for a huge audience who never use Telegram. This is the single most impactful contribution that's not started yet.

**Persistent session storage**
Right now sessions live in memory and reset on restart. A SQLite backend would be a straightforward improvement that makes the bot production-viable for real users.

**New ad templates**
Templates live in `bot/templates/` and are self-contained. Each one receives the same compositor context object and returns an image. Adding a new one doesn't touch anything else. Good first contribution.

**Generative backgrounds**
The current compositor uses gradient/geometric backgrounds because free generative AI background quality is inconsistent. If you find a reliable, free approach to generative backgrounds that works well for product advertising, I want to see it.

## Code style

No strict linter config, but the existing code follows a few conventions:
- Type hints where they add clarity, not everywhere
- Docstrings on public functions, not private helpers
- Comments explain *why*, not *what*
- No abbreviations in variable names unless they're standard (e.g. `img`, `ctx`)

## Commit messages

Plain English, present tense: `Fix Arabic shaping for short words`, `Add SQLite session backend`, `Remove unused fal.ai imports`.

Not: `Fixed stuff`, `WIP`, `Update`.
