# 📐 Architecture Overview

This document provides a visual overview of the **AdBot‑Telegram** system, showing both a high‑level component diagram and a detailed technical flow diagram.

---

## High‑Level Architecture

![High‑Level Architecture](/Users/akhilesh/.gemini/antigravity/brain/25a11ad6-114b-4c24-8a24-215d7c10733f/high_level_architecture_1776790556292.png)

The diagram illustrates the main building blocks:
- **Telegram Bot** – receives user messages and forwards them to the bot handlers.
- **Bot Handlers** – parse commands, images, and copy text.
- **Gemini Client** – contacts the Gemini LLM (with retry logic) to generate ad copy.
- **_effects Module** – shared visual‑effect utilities (auto‑enhance, glow, shadow, gradients).
- **Template Engine** – four market‑grade templates (`hero_center`, `split_screen`, `minimalist`, `bold_poster`).
- **Output** – final JPEG image sent back to the user.

---

## Detailed Technical Flow

![Technical Flow](/Users/akhilesh/.gemini/antigravity/brain/25a11ad6-114b-4c24-8a24-215d7c10733f/technical_flow_1776790575070.png)

The flow chart walks through the request lifecycle:
1. User uploads a product image and copy.
2. Bot receives the update via Telegram API.
3. Handler extracts the payload and calls **Gemini Client**.
4. Gemini Client implements **automatic retry** (up to 3 attempts) on 429 rate‑limit errors.
5. Generated text is passed to the **Template Engine**.
6. The selected template loads the product image and applies visual effects from **_effects.py**.
7. The composed image is encoded as JPEG and returned to the user.

---

*All components are written in pure Python, using Pillow for image manipulation and the official `python‑telegram‑bot` library for Telegram integration.*
