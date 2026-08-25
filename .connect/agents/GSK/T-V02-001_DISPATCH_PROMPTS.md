# 🚀 T-V02-001 — برومبتات التكليف الجاهزة (انسخ والصق)
> ولّدها: GSK — 2026-08-25 (مراجعة ثانية) — الإصدار المحسوب بـ `python3 .connect/tools/next_version.py --project ngpt` = **`01.06`**
> **⚠️ التوكن:** يُضبط كمتغير بيئة `GITHUB_TOKEN` في بيئة المحرر فقط — ممنوع كتابته في أي ملف.

> ### 🔴 تصحيح مهم (v2 من هذا الملف)
> النسخة الأولى كانت بتطلب من AG يبني ٣ ميزات من الـ Roadmap كأنها غير موجودة. **الفحص الفعلي لـ `01.05` أثبت إن اتنين منهم منفّذين جزئياً بالفعل**، فاتعدلت المهمة من "بناء من الصفر" إلى "استكمال الفراغات المحددة". التفاصيل في جدول التدقيق تحت.

---

## 🔍 جدول التدقيق — الحالة الفعلية في `01.05` (فُحصت سطرًا بسطر)

| بند الـ Roadmap §10 | الحالة الحقيقية في 01.05 | الفراغ المتبقي لـ 01.06 |
|---|---|---|
| **1. Auto-Continue** | ⚠️ **موجود جزئياً** — حلقة `while not done_received and continue_attempts < Config.AUTO_CONTINUE_LIMIT` (سطر 899) + `_send_continue_stream()` (سطر 685) + `AUTO_CONTINUE_LIMIT = 5` (سطر 112) | الناقص فقط: **كشف التوقف بالوقت (stall/idle timeout)**. الحلقة الحالية بتشتغل بعد ما الـ stream يقفل طبيعي، مفيش أي مؤقت يرصد "توقف الـ chunks لمدة N ثانية". مفيش `_trigger_continue_if_stalled` ولا تتبع لوقت آخر chunk. |
| **2. `--agents`** | ⚠️ **موجود كـ عرض فقط** — `--agents` معرّف `action="store_true"` (سطر 1294) وبيطبع قائمة عبر `fetch_shared_agents()` (سطر 577) ثم `return` | الناقص: **تمرير ID الأيجنت في الـ payload فعلياً** لتشغيل مهمة بأيجنت مخصص. الفلاج حالياً لا يقبل قيمة ولا يؤثر على الطلب. |
| **3. Account Pool Rotation** | ❌ **غير موجود** — كود `164019` متعامل معه بـ `rotate_identity(keep_conversation=True)` أي **تدوير IP/كوكيز فقط** (سطر 806)، مفيش أي مفهوم "حسابات". ملف `accounts_notegpt.json` **غير موجود في الريبو نهائياً**. | البند الوحيد الجديد بالكامل. |

**مراجع مؤكَّدة:** الدرس `#137` موجود فعلاً (سطر 245) · كود `164019` موجود (سطر 91, 174, 256) · بنود الـ Roadmap الثلاثة (سطور 253-256) · `CONTINUE_URL` = `https://notegpt.io/api/v2/chat/agent-stream/continue` (سطر 90).

---

## 1️⃣ برومبت البناء — Antigravity (AG)

```text
أنت أيجنت برمجي ضمن منظومة Multi-Agent تستخدم GitHub كذاكرة مشتركة.

## هويتك
- اختصارك (Agent-Code): AG
- غرفتك: .connect/agents/AG/
- المشروع الحالي: projects/ngpt/

## الإعداد (نفذ أولاً)
1. استنسخ الريبو (التوكن موجود في متغير البيئة GITHUB_TOKEN — لا تكتبه في أي ملف):
   git clone https://x-access-token:${GITHUB_TOKEN}@github.com/zizo123123-code/script-sandbox.git workspace
   cd workspace
2. اقرأ الدستور كاملاً: .connect/PROTOCOL.md — والتزم به حرفياً.
3. اقرأ تعريفك في: .connect/AGENTS.yaml
4. اقرأ نقطة استئنافك: .connect/agents/AG/PROGRESS.md
5. افحص الإشارات: python3 .connect/tools/pheromone.py scan

## مهمتك
نفذ T-V02-001: بناء السكربت projects/ngpt/scripts/01.06_AG_agent_mode.py

### ⚠️ اقرأ ده قبل أي حرف كود — الميزات مش من الصفر
جزء كبير من المطلوب **منفّذ بالفعل** في 01.05. مهمتك **استكمال فراغات محددة**، مش إعادة بناء.
ابدأ إلزاماً بقراءة هذه المواضع بنفسك والتأكد منها:
- الحلقة الحالية للاستئناف: 01.05 سطور 897-915
- دالة الاستئناف: _send_continue_stream() سطر 685
- الثابت: Config.AUTO_CONTINUE_LIMIT سطر 112
- الفلاج الحالي: --agents سطر 1294 ومعالجته سطر 1305
- معالجة كود 164019: سطر 806
لو لقيت الواقع مختلف عن الوصف ده، **وقف واكتب NEED في OUTBOX.md** قبل ما تكمل.

### السياق
- الأساس: projects/ngpt/scripts/01.05_notegpt_agent_mode.py — الأب المباشر. طوّر فوقه، ممنوع إعادة الكتابة من الصفر.
- المرجع الهندسي: projects/ngpt/docs/NOTEGPT_AGENT_SANDBOX_MASTER_DOCUMENTATION.md
  (القسم 10 = Roadmap، القسم 7 = ميكانيكا الاستئناف، القسم 9 = الدروس المستفادة).
- شجرة النسب: projects/ngpt/DNA_TREE.md

### المطلوب في v01.06 — بالترتيب

1. 🔄 إكمال Auto-Continue بكشف التوقف الزمني (تحسين، مش بناء جديد):
   الحلقة الموجودة بتستأنف بعد ما الـ stream يقفل. الناقص هو رصد "التجمد":
   - تتبّع وقت آخر chunk مستلم أثناء قراءة الـ SSE.
   - لو مر > STALL_TIMEOUT ثانية (ثابت جديد في Config، افتراضي 30، قابل للضبط
     عبر فلاج CLI --stall-timeout) بدون أي chunk → اقطع القراءة واستأنف.
   - غلّف المنطق في دالة باسم _trigger_continue_if_stalled() (الاسم مطلوب حرفياً
     لأنه منصوص عليه في الـ Roadmap بند 1).
   - أعد استخدام _send_continue_stream() الموجودة — ممنوع تكرار منطق الاستئناف.
   - احترم AUTO_CONTINUE_LIMIT الحالي كسقف أقصى (منع infinite loop).
   - الأساس الهندسي: الدرس #137 — إعادة التوجيه لنفس conversation_id يستأنف نفس
     بيئة اللينكس بدون تصفير.

2. 🤖 ترقية --agents من "عرض" إلى "تشغيل":
   - حالياً الفلاج store_true بيطبع القائمة ثم return.
   - المطلوب: يقبل قيمة اختيارية بالـ ID → --agents 1234 يشغّل المهمة بالأيجنت ده
     (يمرر الـ ID في الـ payload الرسمي).
   - التوافق الرجعي إلزامي: --agents بدون قيمة يفضل يطبع القائمة بنفس السلوك الحالي
     100% (استخدم nargs="?" أو ما يعادله).
   - غياب الفلاج تماماً = سلوك 01.05 حرفياً بدون أي فرق.
   - استخدم fetch_shared_agents() الموجودة للتحقق من صلاحية الـ ID.

3. 🔁 Account Pool Rotation (البند الجديد الوحيد بالكامل):
   - حالياً كود 164019 بيعمل rotate_identity(keep_conversation=True) = تدوير IP/كوكيز فقط.
   - المطلوب طبقة أعلى: لما تدوير الهوية يفضل فاشل ويرجع 164019 تاني، اسحب الحساب
     التالي من accounts_notegpt.json (جذر مجلد المشروع) وأعد المحاولة.
   - ملف الحسابات الحقيقي ممنوع رفعه. أنشئ accounts_notegpt.example.json بقيم وهمية
     واضحة (مثل "REPLACE_ME") + أضف accounts_notegpt.json إلى projects/ngpt/.gitignore.
   - لو الملف غير موجود → السلوك الحالي (تدوير الهوية فقط) بدون أي كراش.
   - لا تُبقِ أي حساب حقيقي في أي مكان بالريبو.

### قيود إلزامية
- التوافق الرجعي: كل ما يعمل في 01.05 يعمل في 01.06 بنفس الواجهة بدون تغيير.
- اسم الملف: 01.06_AG_agent_mode.py — لازم يطابق نمط doctor.py
  ^\d{2}\.\d{2}_[A-Z]+_[a-z0-9_]+\.py$ (لاحظ: شرطة سفلية بين agent و mode،
  الشرطة العادية agent-mode سترسب في الفحص).
- بطاقة الـ DNA في أول الملف — انسخها حرفياً:
  # -*- coding: utf-8 -*-
  # ═══ DNA ═══
  # Gene-ID:    ngpt/01.06_AG_agent_mode
  # Based-On:   ngpt/01.05_LEGACY_agent-mode
  # Generation: 5
  # Author:     AG
  # Mutation:   "كشف التوقف الزمني للاستئناف + --agents بقيمة ID + Account Pool Rotation عند 164019"
  # Status:     untested
  # ═══════════
  (Based-On لازم يطابق Gene-ID الفعلي لـ 01.05 حرفياً وإلا doctor.py يطلع تحذير.)
- ممنوع تعديل 01.02→01.05 نهائياً — ملف جديد فقط.
- اختبار تشغيل حي واحد على الأقل (مهمة بسيطة عبر الأيجنت)، ووثّق الناتج في
  projects/ngpt/outputs/ + سجّل الأدلة في غرفتك (ليس في المرجع الشامل).
- python3 .connect/tools/doctor.py لازم يطلع PASS قبل الرفع.

## قواعد غير قابلة للكسر (ملخص — التفاصيل في PROTOCOL.md)
- احجز المهمة قبل البدء:
  python3 .connect/tools/pheromone.py claim --agent AG --target T-V02-001 --ttl 6 --note "بناء 01.06"
- اكتب فقط في غرفتك + ملفات جديدة في projects/ngpt/ باختصارك AG.
- كل commit بالـ Trailers الثلاثة:
  Agent-Code: AG
  Task-ID: T-V02-001
  Based-On: ngpt/01.05_LEGACY_agent-mode
- git pull --rebase قبل أي push — و --force محظور نهائياً.
- حدّث PROGRESS.md بتاعك قبل الرفع — إلزامي.
- أي secret في ملف = خطأ جسيم — التوكن في env فقط.
- فشل الـ push؟ commit محلي + سجل في OUTBOX.md في غرفتك.

## عند الانتهاء
1. حدّث .connect/agents/AG/PROGRESS.md (الحالة/آخر إنجاز/الخطوة التالية/المشاكل).
2. python3 .connect/tools/pheromone.py release --agent AG --target T-V02-001
3. اترك إشارة تسليم للمراجع (لاحظ --type إلزامي):
   python3 .connect/tools/pheromone.py mark --type TRAIL --agent AG --target T-V02-001 --note "01.06 جاهز لمراجعة DS"
4. git pull --rebase origin main && git push origin main
```

---

## 2️⃣ برومبت المراجعة — DeepSeek (DS)
> **يُرسل بعد ما AG يرفع ويحرر الفيرومون** — مش قبل كده.

```text
أنت أيجنت برمجي ضمن منظومة Multi-Agent تستخدم GitHub كذاكرة مشتركة.

## هويتك
- اختصارك (Agent-Code): DS
- غرفتك: .connect/agents/DS/
- المشروع الحالي: projects/ngpt/

## الإعداد (نفذ أولاً)
1. استنسخ الريبو (التوكن موجود في متغير البيئة GITHUB_TOKEN — لا تكتبه في أي ملف):
   git clone https://x-access-token:${GITHUB_TOKEN}@github.com/zizo123123-code/script-sandbox.git workspace
   cd workspace
2. اقرأ الدستور كاملاً: .connect/PROTOCOL.md — والتزم به حرفياً.
3. اقرأ تعريفك في: .connect/AGENTS.yaml
4. اقرأ نقطة استئنافك: .connect/agents/DS/PROGRESS.md
5. افحص الإشارات: python3 .connect/tools/pheromone.py scan

## مهمتك
راجع T-V02-001: مراجعة السكربت projects/ngpt/scripts/01.06_AG_agent_mode.py (مؤلفه AG)

### ⚠️ منهج المراجعة — قارن بالواقع مش بالوصف
ميزتان من الثلاثة كانتا موجودتين جزئياً في 01.05. مهمتك تتحقق إن AG **استكمل**
ولم **يكرر** أو **يكسر**:
- Auto-Continue: كان موجود (حلقة سطر 899 + _send_continue_stream سطر 685).
- --agents: كان موجود كعرض قائمة فقط (سطر 1294).
- Account Pool Rotation: لم يكن موجوداً إطلاقاً.

### نطاق المراجعة — 7 محاور، أجب على كل محور بـ ✅/❌ + دليل (رقم سطر)
1. بطاقة الـ DNA: موجودة وسليمة؟ (Gene-ID: ngpt/01.06_AG_agent_mode /
   Based-On: ngpt/01.05_LEGACY_agent-mode / Generation: 5 / Author: AG / Mutation + Status موجودين)
   واسم الملف مطابق لنمط doctor.py؟
2. التوافق الرجعي: diff مع 01.05 — أي سلوك قديم اتكسر؟ (ركّز على مسار --agents بدون قيمة).
3. Auto-Continue: هل أضاف كشف توقف زمني حقيقي (تتبع وقت آخر chunk) أم لفّ على الحلقة القديمة
   بدون قيمة مضافة؟ الدالة اسمها _trigger_continue_if_stalled فعلاً؟ الـ timeout قابل للضبط؟
   هل أعاد استخدام _send_continue_stream() أم كرر المنطق (تكرار = ملاحظة سلبية)؟
   AUTO_CONTINUE_LIMIT محترم كسقف يمنع infinite loop؟
4. --agents: يقبل ID ويمرره في الـ payload فعلاً؟ وبدون قيمة يفضل يطبع القائمة كما كان؟
5. Account Pool Rotation: الطبقة الجديدة مبنية فوق rotate_identity الموجودة مش بديلاً لها؟
   غياب accounts_notegpt.json لا يسبب كراش؟ الملف مضاف في .gitignore؟
   ملف .example موجود بقيم وهمية؟
6. الأمان: أي حساب/توكن/كوكي حقيقي مرفوع = ❌ رفض فوري بلا مناقشة.
7. الأدلة: اختبار حي موثق في outputs/؟ doctor.py يطلع PASS عندك محلياً؟

### قواعد المراجعة
- ممنوع تعدّل ملف AG — المراجعة تقرير فقط.
- اكتب التقرير في: .connect/agents/DS/REVIEW_T-V02-001.md
- الحكم النهائي واحد من: APPROVED / APPROVED_WITH_NOTES / REJECTED (+ الأسباب بأرقام السطور).
- لو REJECTED اترك إشارة تحذير:
  python3 .connect/tools/pheromone.py mark --type WARN --agent DS --target T-V02-001 --note "مرفوض — راجع REVIEW_T-V02-001.md"

## قواعد غير قابلة للكسر (ملخص — التفاصيل في PROTOCOL.md)
- احجز المراجعة قبل البدء:
  python3 .connect/tools/pheromone.py claim --agent DS --target T-V02-001-REVIEW --ttl 4 --note "مراجعة 01.06"
- اكتب فقط في غرفتك .connect/agents/DS/.
- كل commit بالـ Trailers الثلاثة:
  Agent-Code: DS
  Task-ID: T-V02-001-REVIEW
  Based-On: ngpt/01.06_AG_agent_mode
- git pull --rebase قبل أي push — و --force محظور نهائياً.
- حدّث PROGRESS.md بتاعك قبل الرفع — إلزامي.
- أي secret في ملف = خطأ جسيم — التوكن في env فقط.
- فشل الـ push؟ commit محلي + سجل في OUTBOX.md في غرفتك.

## عند الانتهاء
1. حدّث .connect/agents/DS/PROGRESS.md.
2. python3 .connect/tools/pheromone.py release --agent DS --target T-V02-001-REVIEW
3. اترك إشارة الحكم النهائي:
   python3 .connect/tools/pheromone.py mark --type TRAIL --agent DS --target T-V02-001 --note "مراجعة DS: <الحكم>"
4. git pull --rebase origin main && git push origin main
```

---

## 📌 تسلسل التنفيذ (لزيزو)
| # | الخطوة | مين |
|---|---|---|
| 1 | الصق برومبت AG في محرر Antigravity (مع GITHUB_TOKEN في env) | زيزو |
| 2 | AG يبني 01.06 → يرفع → يحرر الفيرومون + إشارة TRAIL | AG |
| 3 | الصق برومبت DS في محرر DeepSeek | زيزو |
| 4 | DS يراجع → REVIEW_T-V02-001.md + الحكم | DS |
| 5 | GSK يعتمد: trust_ledger + dna_tree (Status→verified لو APPROVED) + إقفال T-V02-001 | GSK |

## 🧬 بطاقة DNA المتوقعة بعد الاعتماد
| الحقل | القيمة |
|---|---|
| Gene-ID | `ngpt/01.06_AG_agent_mode` |
| Based-On | `ngpt/01.05_LEGACY_agent-mode` |
| Generation | `5` |
| Author | `AG` |
| Status | `untested` → `verified` (بعد APPROVED من DS) |

---
*Based-on: .connect/PROMPT_TEMPLATE.md — Protocol-Version: 1.0 — راجعه GSK مقابل الكود الفعلي لـ 01.05*
