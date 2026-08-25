# 🧠 NoteGPT — Models Catalog & Specifications (`models.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **إجمالي النماذج الحقيقية المؤكدة:** 36 نموذجاً  
> **المصدر والدليل:** `projects/ngpt/notegpt_catalog.json` (كلها استجابت بـ `200 OK`).

---

## 📋 جدول الـ 36 نموذجاً الحقيقية المؤكدة

| # | Model ID | زمن الاستجابة الفعلي (s) | يدعم التفكير (`think`) | الحالة | الدليل |
|---|---|---|---|---|---|
| 1 | `deepseek-chat` | 0.61s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 2 | `deepseek-v4-pro` | 0.52s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 3 | `gpt-4.1-mini` | 0.49s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 4 | `gpt-4o` | 0.60s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 5 | `gpt-5-mini` | 0.39s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 6 | `gpt-5` | 0.44s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 7 | `gpt-5.2` | 0.35s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 8 | `gpt-5.1` | 0.40s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 9 | `gpt-5.5` | 0.43s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 10 | `gpt-5.6` | 0.42s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 11 | `claude-sonnet-4-5` | 0.37s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 12 | `claude-3-5-sonnet-20241022` | 0.39s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 13 | `TA/deepseek-ai/DeepSeek-V3` | 1.83s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 14 | `gpt-4o-mini` | 1.50s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 15 | `gpt-4.1` | 1.52s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 16 | `claude-sonnet-5` | 0.55s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 17 | `claude-opus-4-8` | 0.46s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 18 | `claude-opus-4-7` | 0.55s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 19 | `claude-haiku-4-5` | 0.55s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 20 | `gemini-1.5-pro` | 0.40s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 21 | `claude-fable-5` | 0.46s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 22 | `claude-mythos-5` | 0.49s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 23 | `gemini-1.5-flash` | 0.51s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 24 | `gemini-2.5-flash` | 0.56s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 25 | `gemini-2.0-flash-exp` | 0.55s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 26 | `gemini-2.5-pro` | 0.45s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 27 | `gemini-3-flash-preview` | 0.51s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 28 | `deepseek-v4-flash` | 2.96s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 29 | `gemini-3-pro-preview` | 0.52s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 30 | `gemini-3.1-flash-lite` | 0.56s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 31 | `gemini-3.1-pro-preview` | 0.70s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 32 | `gemini-3.5-flash` | 0.61s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 33 | `qwen-2.5-72b` | 0.59s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 34 | `llama-3.3-70b` | 0.73s | — | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 35 | `deepseek-reasoner` | 1.85s | ✅ نعم | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |
| 36 | `TA/deepseek-ai/DeepSeek-R1` | 4.39s | ✅ نعم | `CONFIRMED` | `notegpt_catalog.json` (200 OK) |

---

## 🛠️ تفاصيل الاستدعاء والتمرير
- **معامل تمرير النموذج:** يتم تمرير اسم النموذج في الـ Payload في الحقل: `"model": "<MODEL_ID>"`.
- **النموذج الافتراضي في وضع الـ Agent:** `deepseek-chat` أو `deepseek-v4-pro` لتشغيل ساندبوكس دايتونا وتنفيذ الكود.
