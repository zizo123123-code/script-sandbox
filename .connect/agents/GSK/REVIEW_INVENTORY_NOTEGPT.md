# 🔎 تقرير التحقق — `inventory/notegpt/` (Verification Pass §27)

| البند | القيمة |
|---|---|
| **المراجع** | GSK (Claude/Genspark) |
| **التاريخ** | 2026-08-25 |
| **الهدف** | تنفيذ §27 Verification Pass المطلوب في الـ Gist |
| **الملفات المفحوصة** | 11/11 |
| **مصادر التحقق** | `01.05_notegpt_agent_mode.py` (1342 سطر) · `notegpt_catalog.json` (36 مدخلاً) · 6 ملفات HAR (916 entry) |
| **🚨 الحكم النهائي** | ❌ **REJECTED — VERIFIED_FAIL** |

> **لا يجوز اعتماد هذا الـ Inventory كـ Reference لإعادة بناء الـ Architecture في حالته الحالية.**
> الـ Gist §28 نص حرفياً: *"ممنوع بدء implementation/refactor قبل Verification Pass"* — وهذه هي نتيجة الـ Pass.

---

## 📊 لوحة النتائج

| # | الملف | الحكم | أخطاء حرجة | أخطاء متوسطة |
|---|---|---|---|---|
| 1 | `account.md` | ❌ REJECTED | 3 | 2 |
| 2 | `models.md` | ❌ REJECTED | 3 | 1 |
| 3 | `capabilities.md` | ⚠️ NOTES | 0 | 2 |
| 4 | `generation.md` | ❌ REJECTED | 3 | 1 |
| 5 | `upload.md` | ❌ REJECTED | 2 | 1 |
| 6 | `limits.md` | ❌ REJECTED | 2 | 2 |
| 7 | `errors.md` | ⚠️ NOTES | 1 | 1 |
| 8 | `health.md` | ❌ REJECTED | 2 | 0 |
| 9 | `notes.md` | ✅ PASS | 0 | 1 |
| 10 | `agent.md` | ⚠️ NOTES | 0 | 2 |
| 11 | `provider_summary.md` | ❌ REJECTED | 2 | 1 |
| | **الإجمالي** | **❌ FAIL** | **18** | **16** |

**السبب الجذري الواحد:** الـ Inventory اتكتب **من ذاكرة النموذج ومن الوصف السردي**، مش من قراءة الكود والـ HAR. كل ملف موسوم `CONFIRMED` بأدلة (أرقام سطور / HAR entries) **غير قابلة للتتبع** — وده يخالف §14 (Evidence) في الدستور نفسه.

---

## 🔴 القسم أ — الأخطاء الحرجة (18)

### أ-١ | `models.md`: **٧ نماذج وهمية غير موجودة في الكاتالوج**

الملف يدّعي 36 نموذجاً لكنه يسرد **19 صفاً فقط**، منها **7 مُفبركة**:

| الصف | النموذج المُدّعى | الواقع في `notegpt_catalog.json` |
|---|---|---|
| 11 | `claude-3-7-sonnet` | ❌ غير موجود (الموجود `claude-sonnet-4-5`) |
| 13 | `claude-3-5-haiku` | ❌ غير موجود (الموجود `claude-haiku-4-5`) |
| 14 | `gemini-2.0-flash` | ❌ غير موجود (الموجود `gemini-2.0-flash-exp`) |
| 15 | `gemini-2.0-pro-exp-02-05` | ❌ غير موجود |
| 16 | `qwen-2.5-max` | ❌ غير موجود (الموجود `qwen-2.5-72b`) |
| 17 | `qwen-2.5-coder-32b-instruct` | ❌ غير موجود |
| 18 | `minimax-01` | ❌ غير موجود |

**أثر مباشر:** لو الـ Router الجديد اتبنى على الجدول ده → **7 مسارات تفشل بـ 400** في الإنتاج.

### أ-٢ | `models.md`: **24 نموذجاً حقيقياً محذوف**

النماذج الآتية **موجودة فعلاً بـ `200 OK`** ومحذوفة من التوثيق:
```
claude-sonnet-4-5 · claude-sonnet-5 · claude-opus-4-8 · claude-opus-4-7
claude-haiku-4-5 · claude-fable-5 · claude-mythos-5 · gpt-4o-mini · gpt-4.1
gemini-1.5-pro · gemini-1.5-flash · gemini-2.5-flash · gemini-2.0-flash-exp
gemini-2.5-pro · gemini-3-flash-preview · gemini-3-pro-preview
gemini-3.1-flash-lite · gemini-3.1-pro-preview · gemini-3.5-flash
deepseek-v4-flash · deepseek-reasoner · qwen-2.5-72b · llama-3.3-70b
TA/deepseek-ai/DeepSeek-R1
```
**أثر:** §28 يحذّر حرفياً من فقدان capabilities متاحة — وهنا فُقد **٦٧٪** من الكاتالوج.

### أ-٣ | `models.md`: أزمنة استجابة مغلوطة

| النموذج | مُدّعى | الحقيقي |
|---|---|---|
| `gpt-5.5` | 0.45s | **0.43s** |
| `gpt-5.6` | 0.48s | **0.42s** |
| `claude-3-5-sonnet-20241022` | 0.52s | **0.39s** |
| `TA/deepseek-ai/DeepSeek-V3` | 0.70s | **1.83s** ← فرق 161% |

وأخطر من ده: عمود `Multimodal` كله **تخمين** — الكاتالوج **لا يحتوي حقل vision إطلاقاً**. الحقل الحقيقي الموجود هو `think` (منطق التفكير) وهو **غير موثق نهائياً** رغم إنه مؤكد لـ `deepseek-reasoner` و `TA/deepseek-ai/DeepSeek-R1`.

### أ-٤ | `account.md`: **Clerk لا وجود له — صفر دليل**

- `account.md` يبني كل قصة المصادقة على *"Clerk Authentication"* و *"مزامنة الكوكيز مع `clerk.notegpt.io`"*.
- **الواقع:** بحث في **916 HAR entry** → **`0` ريكويست فيه كلمة clerk**. وبحث في `01.05` → **صفر إشارة لـ Clerk**.
- المصادقة الحقيقية: `POST /api/v1/auth/email/login` (سطر 117 في `01.05`، ومؤكدة في HAR بـ `200`).

### أ-٥ | `account.md`: **اسم الكوكي غلط**

- مُدّعى: `session_token` و `__session` (JWT).
- **الحقيقي** (`01.05` سطر 488): `self.cookies["user_token"] = self.session_token`
  والكوكيز المرافقة: `anonymous_user_id` و `sbox-guid` (سطر 484-485).
- **أثر:** أي كود جديد يبعت `session_token` → **401 مضمون**.

### أ-٦ | `account.md`: صلاحية "30 يوماً" بلا مصدر

لا يوجد أي `expires` أو TTL في الكود ولا في الـ HAR يدعم الرقم. **يجب أن تكون `UNKNOWN`** حسب §13.

### أ-٧ | `generation.md`: **الـ Endpoint الرئيسي غلط**

| المُدّعى | الحقيقي |
|---|---|
| `POST /api/v2/ai-chat/stream` | **`POST /api/v2/chat/stream`** (`01.05` سطر 89 + HAR ×62) |

`/api/v2/ai-chat/stream` **غير موجود في أي HAR entry**. الـ endpoint المذكور في `capabilities.md` كذلك مغلوط بنفس الطريقة.

### أ-٨ | `generation.md`: **حذف endpoint الاستئناف بالكامل**

`POST /api/v2/chat/agent-stream/continue` — موجود في `01.05` سطر 90 ومستخدم **10 مرات** في الـ HAR — **غير مذكور في generation.md إطلاقاً**، رغم إنه العمود الفقري لميزة Auto-Continue.

### أ-٩ | `generation.md`: **أسماء أحداث SSE مُفبركة**

| مُدّعى في التوثيق | الحقيقي في `01.05` |
|---|---|
| `thought` | ❌ غير موجود |
| `tool_call` | ✅ موجود (سطر 716) |
| `tool_result` | ❌ **الحقيقي `tool_call_result`** (سطر 722) |
| `credit` | ❌ **الحقيقي `credit_usage`** (سطر 713) |
| `data: [DONE]` | ❌ **الحقيقي `{"type":"done"}`** (سطر 734) |
| — | ⚠️ **`continue_needed` محذوف** (سطر 911) |
| — | ⚠️ **`agent_tool_limit` محذوف** (سطر 736) |

**أثر:** SSE parser مبني على الجدول ده **لا يقرأ حرفاً واحداً** بشكل صحيح.

### أ-١٠ | `upload.md`: **مسار الرفع كله مُختلق**

- مُدّعى: `POST /api/v2/upload` بـ `multipart/form-data`.
- **الحقيقي** (مؤكد من HAR): مسار **من خطوتين على Alibaba OSS**:
  1. `POST /api/v1/upload/sign-url` → يرجّع `upload_url` موقّع + `object_key`.
  2. `PUT https://nc-product-us-oss.oss-us-west-1.aliyuncs.com/...` → الرفع الفعلي.
- الـ payload الحقيقي للخطوة 1: `{"t":<ts>,"app_id":"notegpt_8c92b6","filename":...,"file_size":...,"headers":{"Content-Type":...},"biz":"ai-chat","sign":"<HMAC>"}`
- **الـ `sign` (توقيع HMAC) غير مذكور إطلاقاً** — وهو أهم عقبة تقنية في المسار كله.

### أ-١١ | `upload.md`: نطاق الـ CDN غلط + "صلاحية دائمة" خطأ

- مُدّعى: `cdn.ng-resource.com/product/resource/...` "صلاحية دائمة".
- **الحقيقي:** `nc-product-us-oss.oss-us-west-1.aliyuncs.com` — والـ URL **موقّت بتوقيع** (`Expires=1787636354`, أي **~10 دقائق**).
- وحد الـ 50MB: **لا دليل** — لا في الكود ولا الـ HAR → يجب `UNKNOWN`.

### أ-١٢ | `limits.md` + `provider_summary.md`: **ادعاء ميزة غير مبنيّة**

كلاهما يؤكد: *"عند `164019` يقوم المحرك بسحب الحساب التالي من `accounts_notegpt.json`"*.
**الواقع** (`01.05` سطر 806-808):
```python
elif code in [164019, 164002, 164003]:
    self.rotate_identity(keep_conversation=True)   # IP + كوكيز فقط
```
**لا وجود لـ `accounts_notegpt.json` في الكود ولا في الريبو.** هذه ميزة **مطلوبة في T-V02-001 كبند جديد** — أي أن الـ Inventory يوثّق المستقبل كأنه حاضر.

### أ-١٣ | `limits.md`: دليل يشير لسطر خطأ + أرقام بلا مصدر

- "الكوتا اليومية 50-100 credit — الدليل: `01.05` سطر 518" → السطر 518 **لا علاقة له بالكوتا** (داخل منطق التوكن).
- `10 RPM` · `60s cooldown` · `00:00 UTC` · `64k-128k context` → **صفر دليل**. الـ HAR **لا يحتوي ولا `429` واحد** (الهيستوجرام: `200`×837, `304`×11, `0`×68 فقط).

### أ-١٤ | `health.md`: **Endpoints مُختلقة**

| مُدّعى | الحقيقي |
|---|---|
| `GET /api/v2/user/info` | ❌ **الحقيقي `/api/v1/userinfo`** |
| `GET /api/v2/plan/quota` | ❌ **الحقيقي `/api/v2/plan-quota`** |
| — | ⚠️ **`/api/v2/user/quota-usage` محذوف** (وهو الأكثر استخداماً: **×212**) |

### أ-١٥ | `health.md`: معيار النجاح غلط

- مُدّعى: النجاح = `{"code": 0, ...}`.
- **الحقيقي:** كود النجاح هو **`100000`** (×728 في الـ HAR). `code: 0` **لا يظهر ولا مرة واحدة**.
- الأكواد الحقيقية المرصودة: `100000` (نجاح) · `164019` (×14) · `164003` (×8، رسالتها الحقيقية `"login expired"`).

### أ-١٦ | `provider_summary.md`: وسم `VERIFIED_COMPLETE` غير مستحق

الملف يعلن نفسه *"`VERIFIED_COMPLETE` 100%"* **قبل** إجراء أي Verification Pass. هذا يخالف §27 و §14 — ويجعل بقية الملفات تبدو معتمدة وهي ليست كذلك.

### أ-١٧ | `errors.md`: `403 Cloudflare` بلا دليل

معقول تقنياً لكن **صفر ظهور** في الـ HAR → يجب `UNKNOWN` أو وسمه كـ *استنتاج من تصميم الكود* لا كـ `CONFIRMED`.
وناقص: **`164002`** (مُعالج في الكود سطر 806) و **`164003`** (مرصود ×8 في HAR).

### أ-١٨ | كل الملفات: **أرقام السطور المرجعية مغلوطة منهجياً**

تحقّقت من كل نطاق سطور مذكور في `capabilities.md` و `account.md`:

| الادعاء | ما يوجد فعلاً في هذا النطاق |
|---|---|
| مصادقة @ 85-92 | تعليق + `class Config` (المصادقة الحقيقية @ 480-495) |
| Fake IP @ 145-156 | `class SourceIngestionHandler` (الحقيقي: `generate_fake_ip` @ **394**) |
| YouTube @ 180-210 | `scan_attachments_folder` (الحقيقي @ 252-258) |
| Chat @ 320-380 | نهاية `build_injected_prompt` + دوال جلسات (الحقيقي: `ask_agent_stream` @ **745**) |
| Streaming @ 390-480 | دوال طباعة/بانر (المعالجة الحقيقية @ 839-911) |
| Vision @ 620-680 | `_finalize_chat_session` (الحقيقي: `image_recognition` @ **1076**) |
| Sandbox @ 700-850 | يبدأ من سطر فاضي — التقاطع جزئي بحت |

**٧ من ٧ نطاقات مغلوطة = 0% دقة.** الأدلة كلها غير قابلة للتتبع.

---

## 🟡 القسم ب — ملاحظات متوسطة (أهمها)

- **ب-١** `capabilities.md`: `Video Generation = CONFIRMED_UNSUPPORTED` — §13 يشترط للـ UNSUPPORTED **دليلاً قاطعاً**؛ "فحص الـ API" ليس دليلاً → يجب `UNKNOWN`.
- **ب-٢** `capabilities.md`: `Image Generation`/`Voice` موسومة `AVAILABLE_BUT_NOT_IMPLEMENTED` بدليل *"واجهة الموقع تدعم"* — بدون رابط/HAR/لقطة. الوسم صحيح احتمالاً لكن الدليل لا يصلح.
- **ب-٣** `capabilities.md`: `Web Search` دليله *"HAR entry 41"* — الترقيم بالفهرس **غير قابل للتتبع** (6 ملفات HAR، أي واحد؟). الأصح: اسم الملف + الـ endpoint.
- **ب-٤** `agent.md`: "Ubuntu 22.04 LTS" و "Python 3.10+" — **صفر دليل** في الكود. أثر منخفض لكن يجب `UNKNOWN`.
- **ب-٥** `agent.md`: ناقص **`/api/v1/agent/share/list`** (مرصود ×16 في HAR، ومستخدم في `01.05` كـ `fetch_shared_agents`) — وهو أساس ميزة `--agents`.
- **ب-٦** `notes.md`: أنضف ملف في المجموعة ✅ — الدرس #137 و `cloudscraper` (سطر 55/473) و `X-Forwarded-For` (سطر 568) **كلها مؤكدة**. الملاحظة الوحيدة: "FIFO آخر 10 مشاريع" غير مؤكد.
- **ب-٧** لا يوجد ملف `streaming.md` منفصل رغم إن §15 يقترحه، والبث هو أعقد جزء في المزود.

---

## ✅ القسم ج — ما نجح فعلاً (للإنصاف)

| البند | الحالة |
|---|---|
| البنية الـ 11 ملفاً مطابقة لـ §15 | ✅ |
| التصنيف الرباعي مستخدم في `capabilities.md` | ✅ |
| `cloudscraper` + `X-Forwarded-For` + الدرس #137 | ✅ مؤكد بالكود |
| `164019` كسبب نفاد الكوتا | ✅ مؤكد بالكود + HAR |
| `image_recognition` / `fetch_url` / `web_search` كأدوات ساندبوكس | ✅ مؤكد (سطر 1076-1078) |
| فصل `agent.md` كـ Module مستقل | ✅ يطابق §5 |
| مخططات Mermaid (شكلياً) | ✅ فكرة جيدة، المحتوى يحتاج تصحيح |

---

## 🛠️ الإجراء المتخذ

أنشأت **`inventory/notegpt/CORRECTIONS.md`** — ملف تصحيحات مستقل يحتوي:
1. القيم الصحيحة الجاهزة للنسخ (endpoints, أسماء الكوكيز, أحداث SSE, أكواد التطبيق).
2. الكاتالوج الكامل الحقيقي بـ 36 نموذجاً.
3. مسار الرفع الحقيقي بخطوتيه.
4. جدول "ادعاء ← تصحيح ← دليل متتبَّع" لكل الـ 18 خطأ.

**لم أعدّل الملفات الـ 11 الأصلية** — لأن مؤلفها أيجنت آخر، والدستور يمنع الكتابة في مخرجات غيري. `CORRECTIONS.md` هو المسار الصحيح: تصحيح موازٍ موثّق.

---

## 📌 التوصية

1. ❌ **لا تعتمد `VERIFIED_PASS`** ولا تبدأ أي refactor بناءً على هذا الـ Inventory.
2. 🔁 **أعد توليد الملفات الـ 11** بقاعدة إلزامية واحدة: *كل رقم وكل اسم endpoint وكل حدث SSE يُنسخ من الكود/HAR بأمر `grep` موثّق — لا من الذاكرة.*
3. ✋ **لا تنتقل للمزود الثاني** (Arena/DeepSeek/Genspark) قبل إغلاق هذا الملف — تكرار نفس المنهج على 3 مزودين يعني 3 أضعاف الأخطاء.
4. 🔒 اقترح إضافة أداة `verify_inventory.py` (مسجّلة أصلاً كـ T-101) تفشل الـ CI لو أي `CONFIRMED` بلا دليل قابل للتتبع.

---

## ⚠️ حدود هذه المراجعة (إفصاح)

- التحقق مبني على **الكود + الكاتالوج + الـ HAR الموجودة في الريبو**. لم أنفّذ أي طلب حي على `notegpt.io`.
- بنود مثل `10 RPM` أو حد `50MB` أو `Ubuntu 22.04` قد تكون **صحيحة واقعياً** — حكمي هو أنها **غير مدعومة بدليل داخل الريبو**، وهذا ما يشترطه §14. الفرق مهم: "غير مُثبت" ≠ "خطأ".
- الـ HAR لا يحتوي `429`/`403`/`504` — لكن غيابها من جلسات محدودة **لا ينفي وجودها**؛ لهذا التوصية هي `UNKNOWN` وليس `UNSUPPORTED`.

---
*GSK — 2026-08-25 · التحقق أُجري بـ `grep`/`python3` على 1342 سطر كود + 36 مدخل كاتالوج + 916 HAR entry*
