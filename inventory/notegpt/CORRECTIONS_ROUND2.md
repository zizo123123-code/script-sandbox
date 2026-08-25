# 🔴 NoteGPT Inventory — تصحيحات الجولة الثانية (`CORRECTIONS_ROUND2.md`)

> **الحالة:** `VERIFIED_FROM_SOURCE` — كل قيمة مستخرجة بأمر موثّق قابل لإعادة التشغيل
> **المُراجِع:** GSK · **التاريخ:** 2026-08-25 · **الجولة:** 2 (بعد `CORRECTIONS.md`)
>
> ⚠️ **ترتيب الأسبقية عند التعارض:**
> `CORRECTIONS_ROUND2.md` (هذا) **>** `CORRECTIONS.md` **>** الملفات الـ 11 الأصلية
>
> **مصادر الحقيقة:**
> - `projects/ngpt/scripts/01.05_notegpt_agent_mode.py` — 1342 سطر
> - `projects/ngpt/scripts/01.06_notegpt_agent_mode.py` — موجود فعلاً (لم يُوثَّق!)
> - `projects/ngpt/notegpt_catalog.json` — 36 مدخلاً
> - `projects/ngpt/har/*.har` — 916 entry

---

## 🚨 0. حرج/أمني — بيانات دخول حقيقية مرفوعة في الريبو

> **هذا البند لم يُذكر في `CORRECTIONS.md` إطلاقاً وهو الأخطر في المراجعة كلها.**
> دستور الـ Inventory §11 يوجب توثيق "Special Requirements" للمصادقة —
> والواقع أن المصادقة **مكشوفة بالكامل في نص صريح**.

### الدليل (أمر واحد يعيد إنتاج النتيجة)

```bash
python3 .connect/tools/secret_scan.py
# ❌ FAIL — 29 سر في 10 ملف   (exit code 1)
```

### النتيجة — **10 ملفات · 29 سراً**

> الفحص الأولي اليدوي وجد 9 ملفات. الأداة الآلية كشفت ملفين إضافيين في
> `tests/` — **وحساباً ثانياً مختلفاً تماماً** لم يكن معروفاً.

| الملف | المحتوى المكشوف |
|---|---|
| `scripts/01.02_notegpt_agent_mode.py` | إيميل + كلمة مرور + توكن جلسة |
| `scripts/01.03_notegpt_agent_mode.py` | إيميل + كلمة مرور + توكن جلسة |
| `scripts/01.05_notegpt_agent_mode.py` | إيميل + كلمة مرور + **توكن حقيقي** |
| `scripts/01.06_notegpt_agent_mode.py` | إيميل + كلمة مرور + **توكن أحدث** |
| `archive/01.01_notegpt_agent_mode_original.py` | نفس النمط |
| `archive/01.02_notegpt_agent_mode.py` | نفس النمط |
| `archive/01.03_notegpt_agent_mode.py` | نفس النمط |
| `archive/01_notegpt_agent_mode copy.py` | نفس النمط |
| **`tests/test_notegpt_agent_mode.py`** | ← **لم يكن في الفحص اليدوي** |
| **`tests/test_deepseek_vs_minimax_agent_duel.py`** | ← **حساب ثانٍ مختلف!** |

**الملخص حسب النوع:**
```
HARDCODED_PASSWORD        ×11
HARDCODED_SESSION_TOKEN   ×11
HARDCODED_EMAIL_CRED      ×10
```

**الأنماط المكشوفة:**
- **حسابان مختلفان** — الأساسي `um66...@emalupe.com` والثاني في ملف الـ duel test
- كلمة مرور ثابتة للحساب الأول في كل الإصدارات + كلمة مرور ثانية مختلفة
- **ثلاث قيم `SESSION_TOKEN` مختلفة** (01.01-01.03 · 01.05 · 01.06)

> ℹ️ `scripts/01.04` **نظيف** — لا يحتوي أي بيانات دخول (تحقق: `grep -n "EMAIL\|PASSWORD" 01.04` = فراغ).

### ⚠️ لا يكفي تعديل الملفات

التوكنات **موجودة في تاريخ Git** بالفعل. أي `git log -p` يستخرجها.
الإصلاح الكامل يتطلب:

1. **فورياً:** إبطال/تغيير كلمة المرور على `notegpt.io` وإسقاط الجلسات (التوكنات تصبح بلا قيمة).
2. نقل القيم إلى متغيرات بيئة (`os.environ`) في السكربتات الجديدة.
3. إنشاء `.env.example` بقيم `REPLACE_ME` + إضافة `.env` للـ `.gitignore`.
4. إضافة فحص أسرار في `doctor.py` (البند 4 أدناه) لمنع التكرار.
5. تنظيف التاريخ (`git filter-repo`) — **قرار المالك**، لأنه يعيد كتابة كل الـ SHAs.

> **التوصية العملية:** ابدأ بالخطوة 1 (إبطال الحساب). دي الخطوة الوحيدة اللي بتلغي الخطر
> فعلياً. باقي الخطوات وقائية لمنع التكرار.

### ثغرة الوسم في `account.md`

| البند | ❌ الوسم الحالي | ✅ الوسم الصحيح |
|---|---|---|
| تخزين البيانات | *(غير مذكور)* | **`CONFIRMED_INSECURE`** — نص صريح في الكود |
| `EMAIL` / `PASSWORD` | *(غير مذكور)* | **`CONFIRMED`** — `01.05:118-119` · مسار `POST /api/v1/auth/email/login` |
| التسجيل التلقائي | *(غير مذكور)* | **`CONFIRMED`** — HAR: `/api/v1/auth/email/register` ×1 + `/register/confirm` ×2 |

---

## 1. 📦 `01.06` موجود فعلاً — والوثائق كلها تتجاهله

### الدليل

```bash
ls projects/ngpt/scripts/
# 01.02 · 01.03 · 01.04 · 01.05 · 01.06  ← خمسة ملفات
python3 .connect/tools/next_version.py --project ngpt
# 01.07   ← وليس 01.06
```

| البند | ❌ الحالة الموثقة | ✅ الواقع |
|---|---|---|
| أحدث سكربت | `01.05` (كل الملفات الـ11 + `CORRECTIONS.md`) | **`01.06_notegpt_agent_mode.py`** (68635 بايت) |
| الإصدار التالي | `01.06` | **`01.07`** |
| مرجع الـ Inventory | `01.05` فقط | يجب تغطية `01.06` أو تبرير الاستثناء صراحة |

**عنوان `01.06` الفعلي:** `NoteGPT Real Agent Sandbox Tester v01.06 (Smart Rebase & Live Browser Sync)`

**ميزات معلنة في ترويسته:**
- Smart Git Pull-Rebase Engine
- المزامنة السحابية المزدوجة مع قائمة المتصفح (Sidebar Recents)
- تقرير تنفيذ شامل + رصيد الحساب
- تدوير سجل المشاريع FIFO (آخر 10 مشاريع) ← *يؤكد ادعاء `notes.md` البند 4
  الذي وُسم `UNKNOWN` في `CORRECTIONS.md` §9 — الدليل موجود في `01.06` لا `01.05`*

### ⚠️ `01.06` سكربت "يتيم" — بلا بطاقة DNA وبلا تسجيل في الشجرة

```bash
grep -n "Gene-ID\|Based-On\|Generation" projects/ngpt/scripts/01.06_notegpt_agent_mode.py
# (فراغ — صفر نتائج)

grep -n "01.06" projects/ngpt/DNA_TREE.md
# (فراغ — غير مسجل)
```

| البند | `01.05` | `01.06` |
|---|---|---|
| بطاقة DNA | ✅ `ngpt/01.05_LEGACY_agent-mode` (سطر 3-4) | ❌ **لا توجد** |
| مسجَّل في `DNA_TREE.md` | ✅ سطر 11-12, 24 | ❌ **غائب** |
| `Based-On` | ✅ `ngpt/01.04_LEGACY_agent-mode` | ❌ **مجهول النسب** |

**الأثر:** لا يمكن لأي أيجنت أن يبني على `01.06` بشكل صحيح — لأنه لا يعرف
الـ Gene-ID الذي يضعه في `Based-On`. هذا **يمنع** إطلاق أي مهمة تستهدف `01.07`
قبل إصلاح بطاقة `01.06` وتسجيلها في الشجرة.

### ✅ تأكيد مستقل من `doctor.py`

```bash
python3 .connect/tools/doctor.py
#   ❌ بطاقة DNA مفقودة (Gene-ID): projects/ngpt/scripts/01.06_notegpt_agent_mode.py
#   النتيجة: ❌ FAIL — 1 خطأ، 0 تحذير
```

> ⚠️ **هذا يعني أن أي تقرير سابق قال `doctor.py = PASS` كان يفحص حالة لا
> تتضمن `01.06`.** الفحص الآن **يفشل** — وهو الصواب. `doctor.py` أثبت أنه
> يعمل بشكل صحيح لفحص الـ DNA (وإن كان لا يفحص الأسرار — البند 4).
>
> **الخلاصة:** الريبو حالياً في حالة `FAIL` رسمياً، وهذا حاجز فعلي يمنع
> إطلاق `T-V02-001` حتى تُصلح بطاقة `01.06`.

### 🔗 الأثر على `T-V02-001` — الحجّة الأساسية تنهار

مهمة `T-V02-001` مبنية على `Based-On: ngpt/01.05` وتهدف لبناء `01.06`.
**لكن `01.06` مبني بالفعل.** لذا المهمة تحتاج إعادة تأصيل:

| البند | القرار المطلوب |
|---|---|
| الإصدار الهدف | `01.06` → **`01.07`** |
| `Based-On` | `ngpt/01.05...` → **الـ Gene-ID الفعلي لـ `01.06`** (غير موجود — يجب إنشاؤه أولاً) |
| `Generation` | 5 → **6** |
| نطاق المهمة | يجب فحص `01.06` أولاً — قد تكون بعض البنود الثلاثة منفَّذة فيه |

> ⚠️ **لا تُطلق `T-V02-001` بصيغتها الحالية قبل حسم هذا البند.**
> السكربت الناتج سيتصادم في التسمية مع `01.06` القائم، ولا يوجد `Based-On`
> صالح ليضعه الأيجنت في بطاقته.

### 📋 خطة الإصلاح المقترحة (مهمة تمهيدية `T-V02-000`)

قبل `T-V02-001`، مهمة صغيرة تُصلح النسب:

1. أضف بطاقة DNA لـ `01.06` بـ `Gene-ID: ngpt/01.06_LEGACY_agent-mode`
   و `Based-On: ngpt/01.05_LEGACY_agent-mode` و `Generation: 5`.
2. سجّل `01.06` في `DNA_TREE.md` (العقدة + السهم + صف الجدول).
3. أعد صياغة `T-V02-001` بالهدف `01.07` والـ `Based-On` الجديد.
4. أعد فحص البنود الثلاثة ضد `01.06` — احتمال أن يكون بعضها منفَّذاً.

---

## 2. 🌊 أحداث SSE — القائمة الحقيقية 13 حدثاً (وليس 7)

`CORRECTIONS.md` §4 صحّح أسماء الأحداث بنجاح، لكن **قائمته النهائية ناقصة 4 أحداث**.

### الدليل

```bash
grep -oE '"type": "[a-z_]+"' projects/ngpt/scripts/01.05_notegpt_agent_mode.py | sort -u
grep -oE '(etype|e_type) == "[a-z_]+"' projects/ngpt/scripts/01.05_notegpt_agent_mode.py | sort -u
```

### القائمة النهائية المصححة

| الحدث | في `CORRECTIONS.md` §4؟ | الحالة |
|---|---|---|
| `credit_usage` | ✅ | `CONFIRMED` |
| `tool_call` | ✅ | `CONFIRMED` |
| `tool_call_result` | ✅ | `CONFIRMED` |
| `done` | ✅ | `CONFIRMED` |
| `continue_needed` | ✅ | `CONFIRMED` |
| `agent_tool_limit` | ✅ | `CONFIRMED` |
| `length` | ✅ | `CONFIRMED` |
| **`text`** | ❌ **مفقود** | `CONFIRMED` — الحدث الأساسي لبث النص! |
| **`reasoning`** | ❌ **مفقود** | `CONFIRMED` — يثبت قدرة الـ think |
| **`sandbox`** | ❌ **مفقود** | `CONFIRMED` |
| **`sandbox_ready`** | ❌ **مفقود** | `CONFIRMED` |
| **`error`** | ❌ **مفقود** | `CONFIRMED` |
| **`info`** | ❌ **مفقود** | `CONFIRMED` |
| `tool_result` | — | ⚠️ **موجود كـ alias** — الكود يقارن بـ `tool_result` **و** `tool_call_result` |

**القائمة النهائية (13 حدثاً + alias):**
```
text · reasoning · sandbox · sandbox_ready · tool_call · tool_call_result
tool_result(alias) · credit_usage · continue_needed · agent_tool_limit
length · error · info · done
```

> ملاحظة مهمة: حدث **`text`** كان مفقوداً من كل الوثائق — وهو الحدث الذي يحمل
> المحتوى الفعلي للرد. أي إعادة بناء تعتمد على `CORRECTIONS.md` وحده كانت
> ستفقد بث النص.

---

## 3. 📤 الرفع — `tmpfiles.org` هو المسار الفعلي في الكود

`CORRECTIONS.md` §5 وثّق مسار `sign-url` + OSS بدقة من الـ HAR ✅.
لكنه لم يوضح أن **الكود لا ينفّذ هذا المسار إطلاقاً**.

### الدليل

```bash
sed -n '170,183p' projects/ngpt/scripts/01.05_notegpt_agent_mode.py
grep -c "sign-url" projects/ngpt/scripts/01.05_notegpt_agent_mode.py   # → 0
```

| المسار | الحالة الحقيقية | الدليل |
|---|---|---|
| `POST /api/v1/upload/sign-url` + `PUT` OSS | ✅ **مسار المتصفح الرسمي** — لكن **غير مطبق في الكود** | HAR ×1 · `grep sign-url` = **0** |
| `POST https://tmpfiles.org/api/v1/upload` | ✅ **المسار الفعلي في السكربت** (طرف ثالث خارجي!) | `01.05:174` |
| `cdn.ng-resource.com/...` | ⚠️ **رابط fallback مبني بـ f-string** — تاريخ مثبّت `2026/08/25` | `01.05:182` |

### ⚠️ ملاحظتان لم تُوثَّقا

1. **تسريب بيانات لطرف ثالث:** كل مرفق يُرفع إلى `tmpfiles.org` (خدمة عامة
   خارجية) قبل تمريره لـ NoteGPT. المرفقات تصبح متاحة عبر رابط عام.
2. **الـ fallback معطوب بنيوياً:** المسار يحتوي `2026/08/25` مكتوباً حرفياً في
   الكود — سيشير لتاريخ خاطئ في أي يوم آخر، والرابط لن يعمل أصلاً لأن الملف
   لم يُرفع لذلك المضيف.

**الوسم الصحيح:** `File Upload` = `CONFIRMED` لكن **`IMPLEMENTED_VIA_THIRD_PARTY`**
وليس عبر مسار المزود الرسمي.

---

## 4. 🛠️ `doctor.py` لا يفحص الأسرار إطلاقاً

### الدليل

```bash
grep -n "secret\|token\|SESSION" .connect/tools/doctor.py
# (فراغ — صفر نتائج)
```

**النتيجة:** `doctor.py` يطبع `✅ PASS — 0 خطأ، 0 تحذير` على ريبو يحتوي
**كلمة مرور وتوكنات حقيقية في 9 ملفات**. الفحص يمرّ لأنه لا يبحث عنها أصلاً.

هذا يخالف قاعدة `PROTOCOL.md`: *"أي secret في ملف = خطأ جسيم"* — القاعدة
موجودة نصاً لكن **بلا أي تطبيق آلي**.

### ✅ الحل المنفَّذ

أُضيفت أداة جديدة: **`.connect/tools/secret_scan.py`**

```bash
python3 .connect/tools/secret_scan.py          # فحص الريبو كله
python3 .connect/tools/secret_scan.py --quiet  # للاستخدام في CI
```

- تكتشف: `SESSION_TOKEN`/`PASSWORD`/`EMAIL` بقيم حرفية · Bearer tokens · مفاتيح API
- تتجاهل: `REPLACE_ME` · `os.environ` · `""` · التعليقات التوضيحية
- ترجع exit code `1` عند وجود أي سر → صالحة للربط بـ CI أو pre-commit

> **ملاحظة:** لم أعدّل `doctor.py` نفسه (ملف بروتوكول مشترك، تعديله يحتاج
> موافقتك). `secret_scan.py` أداة مستقلة جاهزة للدمج متى قررت.

---

## 5. 🧠 `models.md` — الأرقام الدقيقة للاختلاف

`CORRECTIONS.md` §6 أعطى الجدول الصحيح الكامل ✅. هذه إحصائية الفارق للتوثيق:

```bash
python3 - <<'PY'
import json,re
real={x['model'] for x in json.load(open('projects/ngpt/notegpt_catalog.json'))}
md=open('inventory/notegpt/models.md').read()
claimed=[c for c in re.findall(r'\|\s*`([^`]+)`\s*\|',md) if any(ch in c for ch in '-./')]
print("مُدّعى:",len(claimed)," وهمي:",len([c for c in claimed if c not in real]),
      " مفقود:",len(real-set(claimed))," الحقيقي:",len(real))
PY
```

| المقياس | العدد |
|---|---|
| النماذج المُدّعاة في `models.md` | 19 |
| **منها وهمية** (غير موجودة في الكاتالوج) | **7** |
| منها صحيحة | 12 |
| **نماذج حقيقية مفقودة من التوثيق** | **24** |
| الإجمالي الحقيقي في الكاتالوج | **36** |

**نسبة الدقة الفعلية: 12/36 = 33%** — أي أن ثلثي الكاتالوج كان مفقوداً
وسُبع المُوثَّق كان مُختلقاً.

> ⚠️ ملاحظة إضافية: `models.md` يدّعي عموداً `Multimodal` بقيم `✅ Vision`
> لبعض النماذج. **الكاتالوج لا يحتوي أي حقل vision/multimodal** — الحقول
> الحقيقية هي `model` · `status` · `dur` · `think` · `text` فقط.
> كل قيمة في عمود Multimodal = **تخمين بلا دليل** ويجب وسمها `UNKNOWN`.

---

## 6. 📊 جدول الحالة النهائي — ما تغيّر في هذه الجولة

| # | البند | الحالة قبل الجولة 2 | الحالة الصحيحة | الخطورة |
|---|---|---|---|---|
| 0 | بيانات دخول في الكود | *(غير موثق)* | **`CONFIRMED_INSECURE`** — 10 ملفات · 29 سراً · **حسابان** | 🔴 حرج |
| 1 | أحدث سكربت | `01.05` | **`01.06` موجود** · التالي `01.07` | 🔴 حرج |
| 1b | بطاقة DNA لـ `01.06` | *(غير موثق)* | **غائبة** + غير مسجل في `DNA_TREE` | 🔴 حرج |
| 2 | أحداث SSE | 7 أحداث | **13 حدثاً + alias** (`text` كان مفقوداً!) | 🟠 عالٍ |
| 3 | مسار الرفع الفعلي | `sign-url` + OSS | **`tmpfiles.org`** (طرف ثالث) | 🟠 عالٍ |
| 4 | فحص الأسرار آلياً | يُفترض موجوداً | **غير موجود** → أُضيف `secret_scan.py` | 🟠 عالٍ |
| 5 | دقة `models.md` | 7 وهمية (مذكور) | **33% دقة** + عمود Multimodal مُختلق | 🟠 عالٍ |
| 6 | fallback الـ CDN | "CDN رسمي دائم" | **تاريخ مثبّت + مسار معطوب** | 🟡 متوسط |
| 7 | FIFO آخر 10 مشاريع | `UNKNOWN` | **`CONFIRMED`** — الدليل في `01.06` | 🟢 تصحيح لصالح التوثيق |

---

## 7. ✅ ما تأكدت صحته من `CORRECTIONS.md` (تحقق مستقل)

راجعت ادعاءات `CORRECTIONS.md` بأوامر مستقلة — **كلها صحيحة**:

| الادعاء | أمر التحقق | النتيجة |
|---|---|---|
| Clerk غير موجود | `grep -ci clerk 01.05` | **0** ✅ |
| الكوكي الحقيقي `user_token` | `grep -n user_token 01.05` | سطر 488 ✅ |
| `code 100000` = نجاح | تحليل 916 HAR entry | **×728** ✅ |
| `164019` ×14 · `164003` ×8 | نفس التحليل | مطابق تماماً ✅ |
| `code: 0` غير موجود | نفس التحليل | **صفر ظهور** ✅ |
| 7 نماذج وهمية | مقارنة `models.md` بالكاتالوج | **7 وهمية + 24 مفقودة** ✅ |
| `accounts_notegpt.json` غير موجود | `grep -c accounts_notegpt 01.05` | **0** ✅ |
| `AUTO_CONTINUE_LIMIT = 5` | `01.05:112` | مؤكد ✅ |
| `429`/`403`/`504` صفر ظهور | تحليل HAR | مؤكد ✅ |
| Ubuntu 22.04 لا دليل عليه | `grep -ci ubuntu 01.05` | **0** ✅ |
| endpoints الحقيقية | تحليل HAR | مطابقة 100% ✅ |

**الخلاصة:** `CORRECTIONS.md` عمل ممتاز ودقيق فيما غطّاه. الجولة الثانية تكمّل
٤ فراغات لم يغطها + بند أمني حرج.

---

## 8. 🎯 الحكم النهائي

```
الملفات الـ 11 الأصلية:  ❌ REJECTED   — لا تُستخدم كمرجع بأي حال
CORRECTIONS.md:          ✅ VERIFIED_PASS — دقيق فيما غطّى (11/11 ادعاء صحيح)
الحالة المجمّعة:          ⚠️ CONDITIONAL_PASS
```

**الشروط الأربعة للانتقال لمزود ثانٍ:**

1. 🔴 **إبطال الحسابين على `notegpt.io`** وتغيير كلمتَي المرور — الخطر قائم الآن.
   (حسابان لا واحد: الأساسي + الثاني في `tests/test_deepseek_vs_minimax_agent_duel.py`)
2. 🔴 **إصلاح نسب `01.06`** — بطاقة DNA + تسجيل في `DNA_TREE.md` (مهمة `T-V02-000`).
3. 🔴 **إعادة تأصيل `T-V02-001`** — الهدف `01.07` والـ `Based-On` من `01.06`.
4. 🟠 **دمج `secret_scan.py`** في مسار الفحص لمنع تكرار البند 0.

> **لا أنصح بالبدء في مزود ثانٍ قبل الشروط 1-3.** الشرط 1 مخاطرة أمنية
> مفتوحة، والشرطان 2-3 سيُنتجان تصادم أسماء وبطاقة DNA معطوبة لو تُركا.

### ✅ المُنفَّذ في هذه الجولة

| الملف | الحالة | الوصف |
|---|---|---|
| `inventory/notegpt/CORRECTIONS_ROUND2.md` | 🆕 جديد | هذا التقرير |
| `.connect/tools/secret_scan.py` | 🆕 جديد | فاحص أسرار آلي — exit 1 عند وجود سر |
| `projects/ngpt/.env.example` | 🆕 جديد | قالب متغيرات البيئة بقيم `REPLACE_ME` |
| `projects/ngpt/.gitignore` | ✏️ مُحدَّث | أُضيف `.env` · `accounts_notegpt.json` · `cookies.json` |

### ⏸️ ما لم أفعله (يحتاج قرارك)

| البند | السبب |
|---|---|
| تعديل `doctor.py` | ملف بروتوكول مشترك — تعديله يؤثر على كل الأيجنتس |
| حذف الأسرار من السكربتات | سيكسر تشغيل السكربتات الحالية فوراً بلا `.env` مُعبَّأ |
| تنظيف تاريخ Git | يعيد كتابة كل الـ SHAs — قرار مالك الريبو وحده |
| تعديل الملفات الـ 11 | الدستور §الممنوعات: التصحيح يوثَّق ولا يُعاد الكتابة |

---

## 9. 🔍 أوامر إعادة التحقق الكاملة (الجولة 2)

```bash
cd /path/to/script-sandbox

# البند 0 — الأسرار
grep -rn 'SESSION_TOKEN: str = "\|PASSWORD: str = "' projects/ngpt/scripts/*.py projects/ngpt/archive/*.py
python3 .connect/tools/secret_scan.py

# البند 1 — الإصدار الحقيقي
ls projects/ngpt/scripts/
python3 .connect/tools/next_version.py --project ngpt
head -5 projects/ngpt/scripts/01.06_notegpt_agent_mode.py

# البند 2 — أحداث SSE الكاملة
grep -oE '"type": "[a-z_]+"' projects/ngpt/scripts/01.05_notegpt_agent_mode.py | sort -u
grep -oE '(etype|e_type) == "[a-z_]+"' projects/ngpt/scripts/01.05_notegpt_agent_mode.py | sort -u

# البند 3 — مسار الرفع الفعلي
grep -n "tmpfiles\|sign-url\|ng-resource" projects/ngpt/scripts/01.05_notegpt_agent_mode.py

# البند 4 — غياب فحص الأسرار في doctor + الأداة الجديدة
grep -c "secret\|token" .connect/tools/doctor.py   # → 0
python3 .connect/tools/secret_scan.py --quiet       # → ❌ FAIL — 29 سر في 10 ملف

# البند 5 — دقة models.md
python3 -c "import json;print(len(json.load(open('projects/ngpt/notegpt_catalog.json'))))"  # → 36

# البند 1b — بطاقة DNA الغائبة
grep -c "Gene-ID" projects/ngpt/scripts/01.06_notegpt_agent_mode.py  # → 0
grep -c "01.06" projects/ngpt/DNA_TREE.md                            # → 0
```

---
*GSK — 2026-08-25 · الجولة 2 · كل قيمة قابلة لإعادة التحقق بالأوامر أعلاه*
