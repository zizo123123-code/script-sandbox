# 🛠️ NoteGPT — تصحيحات الـ Inventory (`CORRECTIONS.md`)

> **الحالة:** `VERIFIED_FROM_SOURCE` — كل قيمة هنا مستخرجة بأمر `grep`/`python3` موثّق
> **المُصحِّح:** GSK · **التاريخ:** 2026-08-25
> **التقرير الكامل:** `.connect/agents/GSK/REVIEW_INVENTORY_NOTEGPT.md`
>
> ⚠️ **هذا الملف يَسبق الملفات الـ 11 الأخرى عند أي تعارض.**
> مصادر الحقيقة: `projects/ngpt/scripts/01.05_notegpt_agent_mode.py` (1342 سطر) ·
> `projects/ngpt/notegpt_catalog.json` (36 مدخلاً) · `projects/ngpt/har/*.har` (916 entry)

---

## 1. 🔑 المصادقة — القيم الصحيحة

| البند | ❌ الخطأ في `account.md` | ✅ الصحيح | الدليل |
|---|---|---|---|
| مزوّد الهوية | Clerk Authentication | **لا يوجد Clerk إطلاقاً** | `grep -ci clerk` = 0 في الكود وفي 916 HAR entry |
| مسار الدخول | — | `POST /api/v1/auth/email/login` | `01.05:117` + HAR `200 OK` |
| اسم الكوكي | `session_token` / `__session` | **`user_token`** | `01.05:488` |
| كوكيز مرافقة | — | `anonymous_user_id` · `sbox-guid` | `01.05:484-485` |
| هيدر بديل | — | `Authorization: Bearer <token>` | `01.05:573` |
| صلاحية الجلسة | 30 يوماً | **`UNKNOWN`** — لا TTL في أي مصدر | — |
| CSRF | `UNKNOWN` | **`UNKNOWN`** ✅ (الوسم صحيح) | — |
| API Key عام | `CONFIRMED_UNSUPPORTED` | **`UNKNOWN`** — عدم الظهور ≠ عدم الوجود (§13) | — |

```python
# الشكل الحقيقي للكوكيز (01.05:484-488)
self.cookies = {
    "anonymous_user_id": self.anon_user_id,
    "sbox-guid":         self.sbox_guid,
}
if self.session_token:
    self.cookies["user_token"] = self.session_token   # ← الاسم الصحيح
```

---

## 2. 📡 الـ Endpoints الحقيقية

| الغرض | ❌ المُدّعى | ✅ الحقيقي | الدليل |
|---|---|---|---|
| بدء البث | `POST /api/v2/ai-chat/stream` | **`POST /api/v2/chat/stream`** | `01.05:89` · HAR ×62 |
| **الاستئناف** | *(محذوف!)* | **`POST /api/v2/chat/agent-stream/continue`** | `01.05:90` · HAR ×10 |
| تسجيل/تحديث الشات | `/api/v2/ai-chat` | `GET`/`POST`/`PUT /api/v2/ai-chat` ✅ | `01.05:635,681` · HAR ×119/×4/×129 |
| تسجيل الدخول | — | `POST /api/v1/auth/email/login` | `01.05:117` |
| معلومات المستخدم | `GET /api/v2/user/info` | **`GET /api/v1/userinfo`** | HAR ×10 |
| حصة الخطة | `GET /api/v2/plan/quota` | **`GET /api/v2/plan-quota`** | HAR ×212 |
| استهلاك الحصة | *(محذوف!)* | **`GET /api/v2/user/quota-usage`** | HAR ×212 |
| حصة المستخدم | — | `GET /api/v2/user/quota` | HAR ×11 |
| قائمة الأيجنتس | *(محذوف من agent.md)* | **`GET /api/v1/agent/share/list`** | HAR ×16 · `01.05` (`--agents`) |
| توقيع الرفع | `POST /api/v2/upload` | **`POST /api/v1/upload/sign-url`** | HAR `200 OK` |
| صلاحيات الدفع | — | `GET /api/v2/payments/check-user-permissions` | HAR ×6 |

**النطاق الأساسي:** `https://notegpt.io` (`01.05:92`)

---

## 3. 🔢 أكواد التطبيق الحقيقية (JSON `code`)

> ⚠️ **`code: 0` المذكور في `health.md` لا يظهر ولا مرة واحدة في 916 entry.**

| الكود | المعنى | التكرار في HAR | المعالجة في الكود |
|---|---|---|---|
| **`100000`** | ✅ **نجاح** (وليس `0`) | ×728 | — |
| `164019` | نفاد حصة الخطة | ×14 | `01.05:806` → `rotate_identity()` |
| `164003` | **`login expired`** | ×8 | `01.05:806` → `rotate_identity()` |
| `164002` | فشل مصادقة (مُعالج) | 0 | `01.05:806` → `rotate_identity()` |

```python
# المعالجة الفعلية (01.05:806-808)
elif code in [164019, 164002, 164003]:
    self.rotate_identity(keep_conversation=True)   # IP + كوكيز فقط — لا تدوير حسابات
```

### أكواد HTTP — الواقع
هيستوجرام كامل لـ 916 entry: **`200`×837 · `304`×11 · `0`×68** *(الأصفار = LaunchDarkly telemetry)*

| الكود | حالة الوسم الصحيحة |
|---|---|
| `429` | **`UNKNOWN`** — صفر ظهور |
| `403` Cloudflare | **`UNKNOWN`** — صفر ظهور (معقول تصميمياً فقط) |
| `504` | **`UNKNOWN`** — صفر ظهور |
| `401` | **`UNKNOWN`** — الحقيقي هو `164003` بـ HTTP `200` |

---

## 4. 🌊 أحداث الـ SSE الحقيقية

| ❌ المُدّعى في `generation.md` | ✅ الحقيقي | الدليل |
|---|---|---|
| `thought` | **لا وجود له** | — |
| `tool_call` | `tool_call` ✅ | `01.05:716,860` |
| `tool_result` | **`tool_call_result`** | `01.05:722,867` |
| `credit` | **`credit_usage`** | `01.05:713,839,856` |
| `data: [DONE]` | **`{"type":"done"}`** | `01.05:734,885,907` |
| — | **`continue_needed`** ← محذوف | `01.05:911` |
| — | **`agent_tool_limit`** ← محذوف | `01.05:736,887` |
| — | **`length`** ← محذوف | `01.05:736,887` |

**القائمة النهائية الكاملة (7 أحداث):**
```
credit_usage · tool_call · tool_call_result · done · continue_needed · agent_tool_limit · length
```

---

## 5. 📤 مسار الرفع الحقيقي (خطوتان — Alibaba OSS)

> ❌ `POST /api/v2/upload` بـ `multipart/form-data` **غير موجود**.

### الخطوة 1 — طلب توقيع
```http
POST https://notegpt.io/api/v1/upload/sign-url
{
  "t":         1787635752,
  "app_id":    "notegpt_8c92b6",
  "filename":  "verify_5_after_swipe.png",
  "file_size": 110637,
  "headers":   {"Content-Type": "image/png"},
  "biz":       "ai-chat",
  "sign":      "<HMAC signature>"     ← ⚠️ أهم عقبة تقنية، غير موثقة أصلاً
}
```
**الرد:**
```json
{"code": 100000, "message": "success", "data": {
  "object_key": "product/upload/notegpt/ai-chat/2026/08/25/<hash>.png",
  "upload_url": "https://nc-product-us-oss.oss-us-west-1.aliyuncs.com/...?OSSAccessKeyId=...&Expires=1787636354&Signature=..."
}}
```

### الخطوة 2 — الرفع الفعلي
```http
PUT https://nc-product-us-oss.oss-us-west-1.aliyuncs.com/product/upload/notegpt/ai-chat/...
```

| البند | ❌ المُدّعى | ✅ الحقيقي |
|---|---|---|
| المضيف | `cdn.ng-resource.com` | **`nc-product-us-oss.oss-us-west-1.aliyuncs.com`** |
| صلاحية الرابط | "دائمة" | **موقّتة ~10 دقائق** (`Expires=1787636354`) |
| حد الحجم | 50 MB | **`UNKNOWN`** — لا دليل |
| الصيغ المدعومة | PNG/JPG/WEBP/PDF/TXT/MD/CSV | **`UNKNOWN`** — الكود لا يقيّد |

> ℹ️ `01.05:182` يحتوي رابط `cdn.ng-resource.com` **كـ fallback افتراضي فقط**، وليس مسار الرفع.
> `01.05:174` يستخدم `tmpfiles.org` كبديل خارجي.

---

## 6. 🧠 الكاتالوج الحقيقي — 36 نموذجاً

> ملاحظة: `notegpt_catalog.json` يحتوي حقل **`think`** (لا يحتوي حقل vision/multimodal).
> أي عمود Multimodal في `models.md` هو **تخمين غير مدعوم**.

| # | Model ID | zمن (s) | think |
|---|---|---|---|
| 1 | `deepseek-chat` | 0.61 | — |
| 2 | `deepseek-v4-pro` | 0.52 | — |
| 3 | `gpt-4.1-mini` | 0.49 | — |
| 4 | `gpt-4o` | 0.60 | — |
| 5 | `gpt-5-mini` | 0.39 | — |
| 6 | `gpt-5` | 0.44 | — |
| 7 | `gpt-5.2` | 0.35 | — |
| 8 | `gpt-5.1` | 0.40 | — |
| 9 | `gpt-5.5` | **0.43** | — |
| 10 | `gpt-5.6` | **0.42** | — |
| 11 | `claude-sonnet-4-5` | 0.37 | — |
| 12 | `claude-3-5-sonnet-20241022` | **0.39** | — |
| 13 | `TA/deepseek-ai/DeepSeek-V3` | **1.83** | — |
| 14 | `gpt-4o-mini` | 1.50 | — |
| 15 | `gpt-4.1` | 1.52 | — |
| 16 | `claude-sonnet-5` | 0.55 | — |
| 17 | `claude-opus-4-8` | 0.46 | — |
| 18 | `claude-opus-4-7` | 0.55 | — |
| 19 | `claude-haiku-4-5` | 0.55 | — |
| 20 | `gemini-1.5-pro` | 0.40 | — |
| 21 | `claude-fable-5` | 0.46 | — |
| 22 | `claude-mythos-5` | 0.49 | — |
| 23 | `gemini-1.5-flash` | 0.51 | — |
| 24 | `gemini-2.5-flash` | 0.56 | — |
| 25 | `gemini-2.0-flash-exp` | 0.55 | — |
| 26 | `gemini-2.5-pro` | 0.45 | — |
| 27 | `gemini-3-flash-preview` | 0.51 | — |
| 28 | `deepseek-v4-flash` | 2.96 | — |
| 29 | `gemini-3-pro-preview` | 0.52 | — |
| 30 | `gemini-3.1-flash-lite` | 0.56 | — |
| 31 | `gemini-3.1-pro-preview` | 0.70 | — |
| 32 | `gemini-3.5-flash` | 0.61 | — |
| 33 | `qwen-2.5-72b` | 0.59 | — |
| 34 | `llama-3.3-70b` | 0.73 | — |
| 35 | `deepseek-reasoner` | 1.85 | ✅ **نعم** |
| 36 | `TA/deepseek-ai/DeepSeek-R1` | 4.39 | ✅ **نعم** |

### 🚫 نماذج وهمية — احذفها من `models.md`
```
claude-3-7-sonnet · claude-3-5-haiku · gemini-2.0-flash
gemini-2.0-pro-exp-02-05 · qwen-2.5-max
qwen-2.5-coder-32b-instruct · minimax-01
```
**كل الأزمنة أعلاه = `dur` الحقيقي، وكلها `200 OK`.**

---

## 7. ⏳ الحدود — ما هو مُثبت فعلاً

| البند | ❌ المُدّعى | ✅ الحالة الصحيحة |
|---|---|---|
| كوتا يومية | 50-100 credit (دليل: سطر 518) | **`UNKNOWN`** — سطر 518 لا علاقة له بالكوتا |
| RPM | 10 / دقيقة | **`UNKNOWN`** — صفر `429` في HAR |
| Cooldown | 60 ثانية | **`UNKNOWN`** |
| إعادة التعيين | 00:00 UTC | **`UNKNOWN`** |
| حد السياق | 64k-128k | **`UNKNOWN`** |
| نفاد الكوتا | `164019` ✅ | **`CONFIRMED`** — `01.05:806` + HAR ×14 |
| سقف الاستئناف | — | **`AUTO_CONTINUE_LIMIT = 5`** (`01.05:112`) ← مُثبت |

### ⚠️ تصحيح جوهري: تدوير الحسابات **غير مبنيّ**
`limits.md` و `provider_summary.md` يدّعيان سحب الحساب التالي من `accounts_notegpt.json`.
**الواقع:** الملف غير موجود في الريبو، والكود يستدعي `rotate_identity()` = **تدوير IP وكوكيز فقط**.
هذه ميزة **مطلوبة مستقبلاً** في `T-V02-001` (البند 3) — وليست قدرة قائمة.

---

## 8. 🩺 الصحة — القيم الصحيحة

| الفحص | ✅ الـ Endpoint الصحيح | معيار النجاح الصحيح |
|---|---|---|
| Ping | `GET https://notegpt.io/` | `200` |
| صلاحية التوكن | **`GET /api/v1/userinfo`** | `code == 100000` |
| الحصة | **`GET /api/v2/plan-quota`** | `code == 100000` (وليس `code: 0`) |
| الاستهلاك | **`GET /api/v2/user/quota-usage`** | `code == 100000` |
| انتهاء الجلسة | أي endpoint | `code == 164003` → `"login expired"` |

**مثال حقيقي لرد فاشل من الـ HAR:**
```json
{"code": 164003, "message": "login expired"}
```
*لاحظ: يعود بـ HTTP `200` — لذا **لا يمكن** الاعتماد على HTTP status وحده لكشف انتهاء الجلسة.*

---

## 9. ✅ ما تأكد صحته في `notes.md` (أنضف ملف)

| البند | الدليل |
|---|---|
| `cloudscraper` إلزامي | `01.05:55` (import) · `473,551,580` (استخدام) |
| `X-Forwarded-For` لتدوير IP | `01.05:568` + `generate_fake_ip()` @ **394** |
| الدرس #137 — ثبات `conversation_id` | `01.05:531` (`keep_conversation=True`) |
| FIFO آخر 10 مشاريع | **`UNKNOWN`** — غير مؤكد |

---

## 10. 🤖 الأيجنت — تصحيحات

| البند | الحالة |
|---|---|
| أدوات الساندبوكس | ✅ `image_recognition` (`01.05:1076`) · `fetch_url`/`web_search` (`01.05:1078`) |
| مسار العمل `/home/daytona/` | ⚠️ `UNKNOWN` — لا دليل في الكود |
| Ubuntu 22.04 LTS | ⚠️ `UNKNOWN` — لا دليل |
| Python 3.10+ | ⚠️ `UNKNOWN` — لا دليل |
| **قائمة الأيجنتس المشتركة** | ✅ **مفقود من `agent.md`** → `GET /api/v1/agent/share/list` (HAR ×16) |
| سقف أدوات الأيجنت | ✅ حدث `agent_tool_limit` (`01.05:736`) — غير موثق |

---

## 📋 خلاصة الحالات المصححة

| القدرة | الوسم المصحّح | السبب |
|---|---|---|
| Chat / Streaming | `CONFIRMED` | endpoint + أحداث مؤكدة بالكود |
| Agent Sandbox | `CONFIRMED` | `01.05:745-911` |
| Vision (`image_recognition`) | `CONFIRMED` | `01.05:1076` |
| File Upload | `CONFIRMED` (لكن المسار مصحّح) | `sign-url` + OSS PUT |
| YouTube / fetch_url | `CONFIRMED` | `01.05:252-258, 1078` |
| Web Search | `CONFIRMED` | `01.05:1078` |
| **Reasoning (`think`)** | **`CONFIRMED`** ← جديد وغير موثق | `deepseek-reasoner`, `DeepSeek-R1` |
| **Account Pool Rotation** | **`NOT_IMPLEMENTED`** ← كان يُدّعى قائماً | لا وجود لـ `accounts_notegpt.json` |
| Image Generation | `UNKNOWN` | لا دليل قابل للتتبع |
| Audio / STT | `UNKNOWN` | لا دليل قابل للتتبع |
| Video Generation | `UNKNOWN` ← كان `CONFIRMED_UNSUPPORTED` | §13 يشترط دليلاً قاطعاً للنفي |
| Embeddings | `UNKNOWN` ✅ | الوسم كان صحيحاً |

---

## 🔍 أوامر إعادة التحقق (للتتبع)

```bash
cd projects/ngpt

# النماذج الحقيقية
python3 -c "import json;[print(m['model'],m['dur'],m.get('think')) for m in json.load(open('notegpt_catalog.json'))]"

# الـ endpoints في الكود
grep -noE 'https?://notegpt.io[^\"]*' scripts/01.05_notegpt_agent_mode.py | sort -u

# أحداث SSE
grep -nE '== "(credit_usage|tool_call|tool_call_result|done|continue_needed|agent_tool_limit)"' scripts/01.05_notegpt_agent_mode.py

# أكواد التطبيق من الـ HAR
python3 - <<'PY'
import json,glob,collections
c=collections.Counter()
for f in glob.glob('har/*.har'):
    for e in json.load(open(f,encoding='utf-8',errors='replace'))['log']['entries']:
        t=(e['response'].get('content',{}).get('text') or '')
        if t.startswith('{'):
            try: c[json.loads(t).get('code')]+=1
            except: pass
print(c.most_common())
PY

# إثبات غياب Clerk
grep -ci clerk scripts/01.05_notegpt_agent_mode.py
python3 -c "
import json,glob
n=sum('clerk' in e['request']['url'].lower() for f in glob.glob('har/*.har') for e in json.load(open(f,encoding='utf-8',errors='replace'))['log']['entries'])
print('clerk requests:',n)"
```

---
*GSK — 2026-08-25 · كل قيمة في هذا الملف قابلة لإعادة التحقق بالأوامر أعلاه*
