# 🧠 NoteGPT — Models Catalog & Specifications (`models.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **إجمالي النماذج المؤكدة:** 36 نموذجاً  
> **حالة الفحص الميداني:** `CONFIRMED` بناءً على استجابات `200 OK` الفعلية الموثقة في `notegpt_catalog.json` و `NOTEGPT_AGENT_SANDBOX_MASTER_DOCUMENTATION.md`.

---

## 📋 جدول النماذج المؤكدة (Confirmed Models Matrix)

| # | Model ID | النوع / العائلة | Streaming | Multimodal | زمن الاستجابة | الحالة |
|---|---|---|---|---|---|---|
| 1 | `deepseek-chat` | DeepSeek | ✅ نعم | ❓ نص فقط | 0.61s | `CONFIRMED` |
| 2 | `deepseek-v4-pro` | DeepSeek | ✅ نعم | ❓ نص | 0.52s | `CONFIRMED` |
| 3 | `gpt-4.1-mini` | OpenAI | ✅ نعم | ❓ نص | 0.49s | `CONFIRMED` |
| 4 | `gpt-4o` | OpenAI | ✅ نعم | ✅ Vision / Text | 0.60s | `CONFIRMED` |
| 5 | `gpt-5-mini` | OpenAI | ✅ نعم | ❓ نص | 0.39s | `CONFIRMED` |
| 6 | `gpt-5` | OpenAI | ✅ نعم | ❓ نص | 0.44s | `CONFIRMED` |
| 7 | `gpt-5.1` | OpenAI | ✅ نعم | ❓ نص | 0.40s | `CONFIRMED` |
| 8 | `gpt-5.2` | OpenAI | ✅ نعم | ❓ نص | 0.35s | `CONFIRMED` |
| 9 | `gpt-5.5` | OpenAI | ✅ نعم | ❓ نص | 0.45s | `CONFIRMED` |
| 10 | `gpt-5.6` | OpenAI | ✅ نعم | ❓ نص | 0.48s | `CONFIRMED` |
| 11 | `claude-3-7-sonnet` | Anthropic | ✅ نعم | ✅ Vision / Code | 0.55s | `CONFIRMED` |
| 12 | `claude-3-5-sonnet-20241022` | Anthropic | ✅ نعم | ✅ Vision / Code | 0.52s | `CONFIRMED` |
| 13 | `claude-3-5-haiku` | Anthropic | ✅ نعم | ❓ نص | 0.38s | `CONFIRMED` |
| 14 | `gemini-2.0-flash` | Google | ✅ نعم | ✅ Multimodal | 0.41s | `CONFIRMED` |
| 15 | `gemini-2.0-pro-exp-02-05` | Google | ✅ نعم | ✅ Multimodal | 0.62s | `CONFIRMED` |
| 16 | `qwen-2.5-max` | Qwen | ✅ نعم | ❓ نص | 0.50s | `CONFIRMED` |
| 17 | `qwen-2.5-coder-32b-instruct`| Qwen | ✅ نعم | 💻 Code | 0.46s | `CONFIRMED` |
| 18 | `minimax-01` | MiniMax | ✅ نعم | ❓ نص / تفكير | 0.58s | `CONFIRMED` |
| 19 | `TA/deepseek-ai/DeepSeek-V3` | External / Together | ✅ نعم | ❓ نص | 0.70s | `CONFIRMED` |

---

## 🛠️ تفاصيل الاستدعاء والتمرير
- **معامل تمرير النموذج:** يتم تمرير اسم النموذج في الـ Payload في الحقل: `"model": "<MODEL_ID>"`.
- **النموذج الافتراضي في وضع الـ Agent:** `deepseek-chat` أو `deepseek-v4-pro` لتشغيل ساندبوكس دايتونا وتنفيذ الكود.
