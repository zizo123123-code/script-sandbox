# 📝 NoteGPT — Special Notes, Headers & Fingerprints (`notes.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED`

---

## 1. أسرار تخطي الحماية وتفادي الحظر (Cloudflare Fingerprinting)

1. 🥷 **مكتبة `cloudscraper`:**
   - استخدام `cloudscraper.create_scraper()` إلزامي لتوليد بصمات TLS/JA3 متطابقة مع متصفحات Chrome الحقيقية.
2. 🌐 **تدوير الـ IP الديناميكي (`Dynamic Fake IP`):**
   - تمرير هيدر `X-Forwarded-For: <RANDOM_IP>` مع كل ريكويست يمنع خوادم NoteGPT من ربط الطلبات بنفس العنوان الرقمي.
3. 💬 **الدرس الهندسي #137 (Session Continuity):**
   - الحفاظ على نفس الـ `conversation_id` يضمن استمرار نفس جلسة الساندبوكس في دايتونا وعدم إعادة تثبيت المكتبات في كل جولة.
4. 🧹 **تدوير السجلات بنظام FIFO:**
   - الحفاظ على آخر 10 مشاريع فقط لتفادي تضخم مساحة التخزين المحلية.
