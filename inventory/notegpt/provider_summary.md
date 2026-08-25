# 📋 ملخص المزود الشامل: NoteGPT (`provider_summary.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **تاريخ التحديث والتدقيق:** 2026-08-25  
> **حالة الملف المرجعي:** `VERIFIED_FROM_SOURCE` 100%

---

## 📊 1. مصفوفة القدرات والحالات (Capability Matrix)

```text
Provider     Chat   Vision   Reasoning   Files   Agent_Sandbox   Image_Gen   Video
NoteGPT       ✓       ?          ✓         ✓           ✓             ?         ✗
```

* 🟢 **`Chat (Text Generation)`:** `CONFIRMED` — Evidence: مسار `/api/v2/chat/stream` في `01.05:89`.
* 🟢 **`Reasoning (Thinking)`:** `CONFIRMED` — Evidence: مدعوم في `deepseek-reasoner` و `TA/deepseek-ai/DeepSeek-R1` في `notegpt_catalog.json`.
* 🟢 **`Auto-Continue`:** `CONFIRMED` — Evidence: مسار `/api/v2/chat/agent-stream/continue` في `01.05:90`.
* 🟢 **`Agent Sandbox Engine`:** `CONFIRMED` — Evidence: بيئة دايتونا لينكس وأحداث `tool_call` و `tool_call_result` في `01.05:716-722`.
* 🟢 **`Alibaba OSS Upload`:** `CONFIRMED` — Evidence: مسار `/api/v1/upload/sign-url` مع توقيع HMAC في HAR `200 OK`.
* 🔵 **`Vision / Image Gen / Audio`:** `UNKNOWN` — غير مثبتة بحقول صريحة في الكتالوج المتاح.
* 🔴 **`Video Generation`:** `CONFIRMED_UNSUPPORTED` — صفر ظهور في 916 مدخل HAR.

---

## 🔑 2. متطلبات الحساب والجلسات
- **النوع:** Token / Cookie Based عبر كوكي `user_token` وهيدر `Authorization: Bearer`.
- **كود النجاح الرسمي:** `100000` دائماً (ظهر 728 مرة في الـ HAR).
- **أكواد التعافي:** `164019` (نفاد الحصة) و `164003` (انتهاء الدخول) ➔ يتم استدعاء `rotate_identity()`.

---

## 📁 3. فهرس الملفات المرجعية المدققة في `inventory/notegpt/`

| الملف | المحتوى والبيانات الحقيقية | الحالة والدليل (Evidence) |
|---|---|---|
| `account.md` | تفاصيل كوكي `user_token` ودورة حياة الحساب بدون Clerk | `CONFIRMED` — Evidence: `01.05:488` |
| `models.md` | قائمة الـ 36 نموذجاً الحقيقية من `notegpt_catalog.json` | `CONFIRMED` — Evidence: `notegpt_catalog.json` |
| `capabilities.md` | مصفوفة القدرات الحقيقية والتصنيف الرباعي المعتمد | `CONFIRMED` — Evidence: `01.05` + HAR |
| `generation.md` | مسارات `/api/v2/chat/stream` و أحداث الـ SSE السبعة | `CONFIRMED` — Evidence: `01.05:89-90` |
| `upload.md` | مسار الرفع ذو الخطوتين عبر Alibaba OSS و sign-url | `CONFIRMED` — Evidence: HAR `200 OK` |
| `limits.md` | تفاصيل الكوتا والاستهلاك و `GET /api/v2/plan-quota` | `CONFIRMED` — Evidence: HAR ×212 |
| `errors.md` | جدول أكواد التطبيق `100000` و `164019` و `164003` | `CONFIRMED` — Evidence: `01.05:806` |
| `health.md` | فحوصات `GET /api/v1/userinfo` و `GET /api/v2/plan-quota` | `CONFIRMED` — Evidence: HAR ×212 |
| `notes.md` | حيلة `cloudscraper` وتدوير الـ IP والدرس #137 | `CONFIRMED` — Evidence: `01.05:400` |
| `agent.md` | مواصفات ساندبوكس دايتونا ودورة حياة الأيجنت | `CONFIRMED` — Evidence: `01.05:700` |
| `CORRECTIONS.md` | المرجع التفصيلي للمقارنة مع المصدر الأصلي | `VERIFIED` — Evidence: GSK Audit |
| `provider_summary.md` | هذا الملخص المرجعي الشامل | `VERIFIED` — Evidence: verify_inventory.py |
