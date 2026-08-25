# ⚡ NoteGPT — Capabilities Matrix (`capabilities.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **التصنيف:** مصفوفة القدرات الحقيقية ومقارنتها بما هو مطبق في الكود الحالي.

---

## 📊 مصفوفة القدرات (Capabilities Matrix)

| القدرة (Capability) | حالة المزود (Provider Support) | منفذ في الكود الحالي؟ | الدليل / المصدر (Evidence) | ملاحظات تقنية |
|---|---|---|---|---|
| **Text Generation (Chat)** | `CONFIRMED` | ✅ نعم | `01.05` سطر 320-380 | `POST /api/v2/ai-chat/stream` |
| **Streaming (SSE)** | `CONFIRMED` | ✅ نعم | `01.05` سطر 390-480 | معالجة `data: {"type": ...}` |
| **Image Recognition (Vision)** | `CONFIRMED` | ✅ نعم | `01.05` سطر 620-680 | استدعاء أداة `image_recognition` في Daytona |
| **Agent / Sandbox Engine** | `CONFIRMED` | ✅ نعم | `01.05` سطر 700-850 | بيئة Linux كاملة وتنفيذ Python / Shell |
| **File Upload (Images/Docs)** | `CONFIRMED` | ✅ نعم | `01.05` سطر 240-310 | مصفوفة `files: [...]` الأصلية |
| **YouTube Transcript / OCR** | `CONFIRMED` | ✅ نعم | `01.05` سطر 180-210 | دعم روابط اليوتيوب وأداة `fetch_url` |
| **Web Search / Browsing** | `CONFIRMED` | ✅ نعم | HAR entry 41 (`web_search`) | أداة داخلية متاحة للوكلاء |
| **Image Generation (DALL-E)** | `AVAILABLE_BUT_NOT_IMPLEMENTED` | ⏳ غير مطبق | واجهة الموقع تدعم توليد الصور | مدعوم في الـ UI ولم يُبنَ كود مخصص له بعد |
| **Voice / Speech-to-Text** | `AVAILABLE_BUT_NOT_IMPLEMENTED` | ⏳ غير مطبق | تسجيلات الصوت في ملخصات اليوتيوب | متاح عبر ملحقات الموقع |
| **Video Generation** | `CONFIRMED_UNSUPPORTED` | ❌ غير مدعوم | فحص الـ API والـ Endpoints | المنصة مخصصة للملخصات والأيجنتس |
| **Embeddings Endpoint** | `UNKNOWN` | ❓ غير مؤكد | غير موجود في الـ HAR المتاح | قد يكون متاحاً داخلياً لقاعدة المعرفة |

---

## 🎯 خلاصة مقارنة الكود الفعلي بالمتاح:
* **نسبة تغطية الكود الحالي للقدرات الأساسية:** 80% (الشات، الساندبوكس، الرؤية، رفع الملفات، اليوتيوب، البحث).
* **القدرات المتاحة ولم تنفذ بعد:** توليد الصور، والتحويل الصوتي للملخصات.
