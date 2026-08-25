# 🤖 NoteGPT — Cloud Linux Agent & Sandbox System (`agent.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED` كـ Module مستقل وقوي.

---

## 1. مواصفات بيئة الساندبوكس (Daytona Cloud Linux Sandbox)

| الخاصية | المواصفة المؤكدة |
|---|---|
| **نظام التشغيل** | Ubuntu Linux 22.04 LTS (x86_64) |
| **المسار الرئيسي للعمل** | `/home/daytona/` |
| **محرك التشغيل** | Python 3.10+ / Bash Shell |
| **الأدوات المدمجة في البيئة** | `bash`, `python3`, `git`, `curl`, `wget`, `image_recognition`, `web_search`, `fetch_url` |
| **الوصول للإنترنت** | ✅ متاح ومباشر (تحميل مكتبات `pip`، استنساخ من `GitHub`، واستدعاء الـ APIs) |

---

## 2. دورة حياة تنفيذ مهام الأيجنت (3-Phase Agent Lifecycle)

1. **المرحلة 1 (Init & Planning):**
   - استلام التكليف، تحليل المشكلة، ووضع خطة التنفيذ خطوة بخطوة.
2. **المرحلة 2 (Agent Execution Loop):**
   - كتابة الكود محلياً، تشغيل الأوامر عبر أداة `bash`، التقاط الـ stdout/stderr، وتصحيح الأخطاء تلقائياً.
3. **المرحلة 3 (Delivery & Upload):**
   - حفظ الملفات والتقارير في مسار العمل، ورفعها لـ CDN المنصة، وتسليم الرد النهائي الموثق بالأدلة.
