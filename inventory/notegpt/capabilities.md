# ⚡ NoteGPT — Capabilities Matrix (`capabilities.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED` بناءً على فحص كود `01.05` والـ 36 نموذجاً في `notegpt_catalog.json`.

---

## 📊 مصفوفة القدرات الحقيقية (Capabilities Matrix)

| القدرة (Capability) | حالة المزود (Provider Support) | منفذ في الكود الحالي؟ | الدليل / المصدر (Evidence) | ملاحظات تقنية |
|---|---|---|---|---|
| **Text Generation (Chat)** | `CONFIRMED` | ✅ نعم | `01.05:89` (`/api/v2/chat/stream`) | استجابة SSE Stream كاملة |
| **Auto-Continue** | `CONFIRMED` | ✅ نعم | `01.05:90` (`/api/v2/chat/agent-stream/continue`) | استئناف البث التلقائي |
| **Reasoning / Thinking Models** | `CONFIRMED` | ✅ نعم | `notegpt_catalog.json` (`think: true`) | نماذج R1 و DeepSeek Reasoner |
| **Agent / Sandbox Engine** | `CONFIRMED` | ✅ نعم | `01.05:700-850` | بيئة دايتونا لينكس وأداة `bash` |
| **Tool Calling (`tool_call`)** | `CONFIRMED` | ✅ نعم | `01.05:716` و `01.05:722` | تشغيل أدوات داخل الساندبوكس |
| **Custom Agents (`--agents`)** | `CONFIRMED` | ✅ نعم | HAR ×16 (`/api/v1/agent/share/list`) | قائمة الوكلاء المخصصين |
| **Vision / Image Input** | `UNKNOWN` | ⏳ fallback | `01.05:182` | لا يوجد حقل مخصص في الكتالوج |
| **Alibaba OSS Signed Upload** | `CONFIRMED` | ⏳ يدوي في الكود | HAR `POST /api/v1/upload/sign-url` | رفع الصور بتوقيع HMAC |
| **Image Generation** | `UNKNOWN` | ❌ غير مطبق | غير مثبت بـ Endpoint صريح في الـ HAR | يحتاج استكشاف إضافي |
| **Audio / Speech-to-Text** | `UNKNOWN` | ❌ غير مطبق | غير مثبت في الـ HAR الحالي | يحتاج استكشاف إضافي |
| **Video Generation** | `CONFIRMED_UNSUPPORTED` | ❌ غير مدعوم | لا يوجد أي أثر في 916 مدخل HAR | المنصة للنصوص والأيجنتس فقط |
