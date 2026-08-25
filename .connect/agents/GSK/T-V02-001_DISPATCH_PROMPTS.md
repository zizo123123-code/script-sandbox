# 🚀 T-V02-001 — برومبتات التكليف الجاهزة (انسخ والصق)
> ولّدها: GSK — 2026-08-25 — الإصدار المحسوب بـ `next_version.py --project ngpt` = **`01.06`**
> **⚠️ التوكن:** يُضبط كمتغير بيئة `GITHUB_TOKEN` في بيئة المحرر فقط — ممنوع كتابته في أي ملف.

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
5. افحص الإشارات: python .connect/tools/pheromone.py scan

## مهمتك
نفذ T-V02-001: بناء السكربت projects/ngpt/scripts/01.06_AG_agent-mode.py

### السياق (اقرأ قبل كتابة أي سطر)
- الأساس: projects/ngpt/scripts/01.05_notegpt_agent_mode.py — هذا هو الأب المباشر، لا تعيد كتابته من الصفر بل طوّر فوقه.
- المرجع الهندسي الشامل: projects/ngpt/docs/NOTEGPT_AGENT_SANDBOX_MASTER_DOCUMENTATION.md
  (خصوصاً القسم 10 — Extensibility Roadmap، والقسم 9 — الدروس المستفادة).
- شجرة النسب: projects/ngpt/DNA_TREE.md

### المطلوب في v01.06 (ثلاث ميزات من الـ Roadmap — بالترتيب)
1. 🔄 Auto-Continue المدمج:
   دالة _trigger_continue_if_stalled() داخل الكلاينت — لو الـ SSE Stream توقف
   قبل وصول `data: [DONE]` (timeout قابل للضبط، افتراضي 30 ثانية بدون chunks)،
   يرسل السكربت طلب استئناف تلقائياً على نفس conversation_id (الدرس #137:
   إعادة التوجيه لنفس المحادثة يستأنف نفس بيئة اللينكس بدون تصفير).
2. 🤖 دعم الـ 50 أيجنت المخصص:
   فلاج CLI جديد --agents يقبل ID الوكيل (Deep Research / محلل بيانات / ...)
   ويمرره في الـ payload الرسمي. لو الفلاج غايب، السلوك الحالي يفضل كما هو 100%.
3. 🔁 Account Pool Rotation:
   عند استقبال كود 164019 (نفاد الحصة)، السكربت يسحب الحساب التالي من ملف
   accounts_notegpt.json (نفس مجلد المشروع، أنشئ accounts_notegpt.example.json
   كنموذج — ممنوع رفع حسابات حقيقية) ويعيد المحاولة تلقائياً بدون انقطاع.

### قيود إلزامية
- التوافق الرجعي: كل ما كان يعمل في 01.05 يعمل في 01.06 بدون أي تغيير في الواجهة.
- بطاقة الـ DNA في أول الملف — انسخها حرفياً:
  # -*- coding: utf-8 -*-
  # ═══ DNA ═══
  # Gene-ID:    ngpt/01.06_AG_agent-mode
  # Based-On:   ngpt/01.05_LEGACY_agent-mode
  # Generation: 5
  # Author:     AG
  # Mutation:   "Auto-Continue + دعم --agents للوكلاء المخصصين + Account Pool Rotation (كود 164019)"
  # Status:     untested
  # ═══════════
- ممنوع تعديل 01.02→01.05 نهائياً — ملف جديد فقط.
- اختبار تشغيل حي واحد على الأقل (مهمة بسيطة عبر الأيجنت) ووثّق الناتج في
  projects/ngpt/outputs/ + حدّث قسم Test Proofs في غرفتك (ليس في المرجع الشامل).
- python .connect/tools/doctor.py لازم يطلع PASS قبل الرفع.

## قواعد غير قابلة للكسر (ملخص — التفاصيل في PROTOCOL.md)
- احجز المهمة قبل البدء:
  python .connect/tools/pheromone.py claim --agent AG --target T-V02-001 --ttl 6 --note "بناء 01.06"
- اكتب فقط في غرفتك + ملفات جديدة في projects/ngpt/scripts/ باختصارك AG.
- التسمية: 01.06_AG_agent-mode.py — الرقم محسوب مسبقاً من next_version.py.
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
2. python .connect/tools/pheromone.py release --agent AG --target T-V02-001
3. اترك إشارة تسليم للمراجع:
   python .connect/tools/pheromone.py mark --agent AG --target T-V02-001 --note "01.06 جاهز لمراجعة DS"
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
5. افحص الإشارات: python .connect/tools/pheromone.py scan

## مهمتك
راجع T-V02-001: مراجعة السكربت projects/ngpt/scripts/01.06_AG_agent-mode.py (مؤلفه AG)

### نطاق المراجعة — 6 محاور، أجب على كل محور بـ ✅/❌ + دليل
1. بطاقة الـ DNA: موجودة وسليمة؟ (Gene-ID: ngpt/01.06_AG_agent-mode /
   Based-On: ngpt/01.05_LEGACY_agent-mode / Generation: 5 / Author: AG)
2. التوافق الرجعي: قارن diff مع 01.05 — هل أي سلوك قديم اتكسر؟
3. Auto-Continue: منطق كشف التوقف سليم؟ الـ timeout قابل للضبط؟ فيه حد أقصى
   لمحاولات الاستئناف يمنع infinite loop؟
4. --agents: الفلاج اختياري فعلاً؟ غيابه = سلوك 01.05 بالظبط؟
5. Account Pool Rotation: كود 164019 يتعامل معه صح؟ accounts_notegpt.json
   مش مرفوع بحسابات حقيقية؟ (وجود secrets = رفض فوري للمراجعة)
6. الأمان العام: مفيش أي توكن/باسورد/كوكي حقيقي في أي ملف اترفع.

### قواعد المراجعة
- ممنوع تعدّل ملف AG — المراجعة تقرير فقط.
- اكتب التقرير في: .connect/agents/DS/REVIEW_T-V02-001.md
- الحكم النهائي واحد من: APPROVED / APPROVED_WITH_NOTES / REJECTED (+ الأسباب).
- لو REJECTED: اترك إشارة تحذير:
  python .connect/tools/pheromone.py mark --agent DS --target T-V02-001 --note "مرفوض — راجع REVIEW_T-V02-001.md"

## قواعد غير قابلة للكسر (ملخص — التفاصيل في PROTOCOL.md)
- احجز المراجعة قبل البدء:
  python .connect/tools/pheromone.py claim --agent DS --target T-V02-001-REVIEW --ttl 4 --note "مراجعة 01.06"
- اكتب فقط في غرفتك .connect/agents/DS/.
- كل commit بالـ Trailers الثلاثة:
  Agent-Code: DS
  Task-ID: T-V02-001-REVIEW
  Based-On: ngpt/01.06_AG_agent-mode
- git pull --rebase قبل أي push — و --force محظور نهائياً.
- حدّث PROGRESS.md بتاعك قبل الرفع — إلزامي.
- أي secret في ملف = خطأ جسيم — التوكن في env فقط.
- فشل الـ push؟ commit محلي + سجل في OUTBOX.md في غرفتك.

## عند الانتهاء
1. حدّث .connect/agents/DS/PROGRESS.md.
2. python .connect/tools/pheromone.py release --agent DS --target T-V02-001-REVIEW
3. اترك إشارة الحكم النهائي:
   python .connect/tools/pheromone.py mark --agent DS --target T-V02-001 --note "مراجعة DS: <الحكم>"
4. git pull --rebase origin main && git push origin main
```

---

## 📌 تسلسل التنفيذ (لزيزو)
| # | الخطوة | مين |
|---|---|---|
| 1 | الصق برومبت AG في محرر Antigravity (مع GITHUB_TOKEN في env) | زيزو |
| 2 | AG يبني 01.06 → يرفع → يحرر الفيرومون + إشارة تسليم | AG |
| 3 | الصق برومبت DS في محرر DeepSeek | زيزو |
| 4 | DS يراجع → REVIEW_T-V02-001.md + الحكم | DS |
| 5 | GSK يعتمد: trust_ledger + dna_tree (Status→verified لو APPROVED) + إقفال T-V02-001 | GSK |

---
*Based-on: .connect/PROMPT_TEMPLATE.md — Protocol-Version: 1.0*
