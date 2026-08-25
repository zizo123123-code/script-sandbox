# ⚠️ NoteGPT — Error Codes & Recovery Strategies (`errors.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED`

---

## 📋 جدول أكواد الأخطاء الشائعة وحلولها

| الكود (HTTP / App Code) | نوع الخطأ | السبب الفني | استراتيجية الحل البرمجي |
|---|---|---|---|
| **`164019`** | `PLAN_QUOTA_EXCEEDED` | نفاد رصيد الكريديت للحساب الحالي | تدوير الحساب فوراً وسحب التالي من Pool |
| **`401 Unauthorized`** | `AUTH_EXPIRED` | انتهاء صلاحية كوكي `session_token` | تجديد التوكن عبر Clerk أو تحديث ملف الكوكيز |
| **`403 Forbidden`** | `CLOUDFLARE_BLOCK` | اعتراض Cloudflare لبصمة الريكويست | استخدام `cloudscraper` وتدوير الـ IP عبر `X-Forwarded-For` |
| **`429 Too Many Requests`** | `RATE_LIMITED` | إرسال طلبات كثيرة في وقت قصير | تطبيق Exponential Backoff وانتظار 15-30 ثانية |
| **`504 Gateway Timeout`** | `STREAM_STALLED` | تعليق الـ SSE Stream قبل `data: [DONE]` | تفعيل `Auto-Continue` على نفس `conversation_id` |
| **`500 Internal Error`** | `SANDBOX_FAILURE` | خطأ داخلي في تهيئة بيئة دايتونا | إعادة المحاولة مع جلسة شات جديدة |
