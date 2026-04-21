# 📋 AdBot — Session Handoff Note
> **Date**: 20 April 2026  
> **Status**: Paused — Resume Tomorrow

---

## 🟢 What's Working Right Now (Live)

| Component | Status | Notes |
|---|---|---|
| Telegram bot | ✅ Working | Run: `source venv/bin/activate && python -W ignore telegram_bot.py` |
| Gemini 2.5 Flash | ✅ Working | JSON parsing fixed (4-stage robust parser) |
| Pollinations FLUX | ✅ Working | Upgraded from SDXL → FLUX model |
| Vision DNA pipeline | ✅ Working | Gemini extracts product DNA into `visual_style` dict |
| Negative prompts | ✅ Working | Industry-calibrated per business type |
| Telegram Stars | ✅ Working | Full payment flow end-to-end |
| Canva affiliate | ✅ Working | Tagged links in every delivery |

---

## 🐛 Bug Fixed Today

**Error**: `❌ Gemini error: Expecting value: line 28 column 22 (char 2192)`

**Root cause**: 2 compounding issues:
1. Gemini 2.5 Flash outputs `<think>...</think>` tokens before JSON — old parser failed
2. `COPY_SCHEMA` had long instruction text inside JSON values — confused Gemini

**Fix applied**: 
- `bot/gemini_client.py` → 4-stage robust JSON parser (strips thinking tokens, fences, regex fallback)
- `bot/prompts.py` → Clean schema with `"string"` placeholders, instructions below the JSON block
- `max_output_tokens` increased from `2048` → `4096`

---

## 📁 Files Changed Today

### Code Changes
| File | Change |
|---|---|
| `config.py` | `POLLINATIONS_URL` → `POLLINATIONS_BASE + POLLINATIONS_PARAMS` with `model=flux` |
| `bot/prompts.py` | **Full rewrite** — Vision DNA pipeline, rich visual_style schema, negative prompts |
| `bot/image_client.py` | **Full rewrite** — FLUX model, dict prompt support, negative prompt URL encoding |
| `bot/gemini_client.py` | **Full rewrite** — Robust 4-stage JSON parser, 4096 token limit |
| `bot/image_client_fal.py` | **NEW** — fal.ai image-to-image reference (not active, for future use) |
| `generate_pitch_deck.py` | **NEW** — Generates the investor PPTX |

### Documentation Created
| File | Purpose |
|---|---|
| `docs/PROJECT_OVERVIEW.md` | Architecture, user journey, revenue model |
| `docs/CODE_WALKTHROUGH.md` | Every file explained with code snippets |
| `docs/IMAGE_PIPELINE.md` | Root cause analysis + Vision DNA solution |
| `docs/FAL_AI_UPGRADE.md` | Step-by-step fal.ai upgrade guide |
| `docs/NEXT_GEN_PROPOSAL.md` | V2 concept: real product compositor + WhatsApp + multilingual |
| `docs/TECHNICAL_REQUIREMENTS.md` | 8 UML diagrams, API contracts, global launch plan, full cost model |
| `docs/AdBot_Investor_Pitch_Deck.pptx` | 14-slide investor presentation |

---

## 🔜 Where to Continue Tomorrow

### Immediate Next Step — Phase 1 Build
The proposal and architecture are complete. Next session should start with:

```
1. Install rembg for real product background removal:
   pip install rembg onnxruntime
   
2. Create bot/bg_remover.py (rembg wrapper)

3. Create bot/compositor.py (Pillow ad layout engine)
   - 3 templates: hero_center, split_screen, minimalist
   - Text rendering with Noto fonts
   
4. Create bot/font_manager.py (multilingual font handling)

5. Update bot/handlers/image.py to call compositor instead of Pollinations
   (Pollinations stays as fallback when no photo uploaded)

6. Test with 3 products: food, fashion, tech
```

### To Start the Bot Tomorrow
```bash
cd "/Users/akhilesh/Documents/Add AI agent/AdBot-Telegram"
source venv/bin/activate
python -W ignore telegram_bot.py
```

### Open Questions for Tomorrow
- [ ] Which 3 templates to build first? (Proposal has 6 designs)
- [ ] Hindi or Arabic as first non-English language?
- [ ] Railway deployment or continue testing locally first?
- [ ] Add the Canva affiliate tag to `.env` (currently empty = no commission earned)

---

## 💰 Quick Reference — Revenue You're Missing Right Now

```
Canva Affiliate:  CANVA_AFFILIATE_TAG= is EMPTY in .env
Action:           Sign up at canva.com/affiliates → paste tag in .env → restart bot
Potential:        Every Canva click could earn 25-80% commission
```

---

*Good night! Everything is saved. Resume tomorrow with Phase 1 build.*
