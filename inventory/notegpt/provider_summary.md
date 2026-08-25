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

* 🟢 **`Chat (Text Generation)`:** `CONFIRMED` — مسار `/api/v2/chat/stream` في `01.05:89`.
* 🟢 **`Reasoning (Thinking)`:** `CONFIRMED` — مدعوم في `deepseek-reasoner` و `TA/deepseek-ai/DeepSeek-R1`.
* 🟢 **`Auto-Continue`:** `CONFIRMED` — مسار `/api/v2/chat/agent-stream/continue` في `01.05:90`.
* 🟢 **`Agent Sandbox Engine`:** `CONFIRMED` — بيئة دايتونا لينكس مع أحداث `tool_call` و `tool_call_result`.
* 🟢 **`Alibaba OSS Upload`:** `CONFIRMED` — مسار `/api/v1/upload/sign-url` مع توقيع HMAC.
* 🔵 **`Vision / Image Gen / Audio`:** `UNKNOWN` — غير مثبتة بحقول صريحة في الكتالوج المتاح.
* 🔴 **`Video Generation`:** `CONFIRMED_UNSUPPORTED` — صفر ظهور في 916 مدخل HAR.

---

## 🔑 2. متطلبات الحساب والجلسات
- **النوع:** Token / Cookie Based عبر كوكي `user_token` وهيدر `Authorization: Bearer`.
- **كود النجاح الرسمي:** `100000` دائماً (ظهر 728 مرة في الـ HAR).
- **أكواد التعافي:** `164019` (نفاد الحصة) و `164003` (انتهاء الدخول) ➔ يتم استدعاء `rotate_identity()`.

---

## 📁 3. فهرس الملفات المرجعية المدققة في `inventory/notegpt/`

| الملف | المحتوى والبيانات الحقيقية | الحالة |
|---|---|---|
| `account.md` | تفاصيل كوكي `user_token` ودورة حياة الحساب بدون Clerk | `CONFIRMED` |
| `models.md` | قائمة الـ 36 نموذجاً الحقيقية من `notegpt_catalog.json` | `CONFIRMED` |
| `capabilities.md` | مصفوفة القدرات الحقيقية والتصنيف الرباعي المعتمد | `CONFIRMED` |
| `generation.md` | مسارات `/api/v2/chat/stream` و أحداث الـ SSE السبعة | `CONFIRMED` |
| `upload.md` | مسار الرفع ذو الخطوتين عبر Alibaba OSS و sign-url | `CONFIRMED` |
| `limits.md` | تفاصيل الكوتا والاستهلاك و `GET /api/v2/plan-quota` | `CONFIRMED` |
| `errors.md` | جدول أكواد التطبيق `100000` و `164019` و `164003` | `CONFIRMED` |
| `health.md` | فحوصات `GET /api/v1/userinfo` و `GET /api/v2/plan-quota` | `CONFIRMED` |
| `notes.md` | حيلة `cloudscraper` وتدوير الـ IP والدرس #137 | `CONFIRMED` |
| `agent.md` | مواصفات ساندبوكس دايتونا ودورة حياة الأيجنت | `CONFIRMED` |
| `CORRECTIONS.md` | المرجع التفصيلي للمقارنة مع المصدر الأصلي | `VERIFIED` |
| `provider_summary.md` | هذا الملخص المرجعي الشامل | `VERIFIED` |
