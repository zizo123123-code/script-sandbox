# 🔗 TRACEABILITY_MATRIX.md — مصفوفة التتبع
## ربط كل قرار/مهمة بمصدرها في وثائق الجولات الأصلية

> **الهدف:** أي حد يسأل "القرار ده جه منين؟" يلاقي الإجابة هنا في ثواني.
> **المصادر:**
> - `[R1..R11]` = الجولات 1-11 في `connect-now-lab/01.02_Multi-Agent-System-...md`
> - `[LAB2]` = `connect-now-lab/Multi-Agent-System-...md`
> - `[MGP]` = `MASTER_GIT_SANDBOX_PROMPT_TEMPLATE.md`
> - `[CLR]` = مراجعة Claude/Genspark 2026-08-25

---

## 1️⃣ القرارات المعمارية ← مصادرها

| # | القرار المعتمد | المصدر الأصلي | تعديل Claude | المهمة المنفذة |
|---|----------------|----------------|---------------|----------------|
| D-01 | GitHub كذاكرة حية مشتركة + نقاط استئناف | [R1] [MGP] | بدون تعديل ✅ | كل المنظومة |
| D-02 | غرفة معزولة لكل أيجنت | [R3] (connect_antigravity/...) | نقل الغرف لـ `.connect/agents/{CODE}/` بالاختصار بدل الروت بالاسم الكامل | T-001, T-005, T-006 |
| D-03 | التسمية `{NN.NN}_{CODE}_{slug}.py` + `# Based-on:` | [R2] [R5] | بدون تعديل ✅ | T-009, PROTOCOL |
| D-04 | ملف تعريف الأيجنتات `agents.yaml` | [R9] (.connect/agents.yaml) | تبسيط الحقول + إضافة `status: active/reserved` | T-002 |
| D-05 | مصفوفة الأكواد (AG, DS, GM, GPT, CL, CP) | [R11] | بدون تعديل ✅ | T-002 |
| D-06 | البرومبت الديناميكي الموحد بالمتغيرات | [R5] [MGP] | اختصار وتقليل الحشو | T-004 |
| D-07 | `pull --rebase` + حظر `--force` | [R3] [R5] | بدون تعديل ✅ | PROTOCOL |
| D-08 | قالب PROGRESS (حالة/إنجاز/التالي/مشاكل) | [R5] بند 7 | بدون تعديل ✅ | T-005, PROGRESS.md |
| D-09 | مجلد `projects/` متعدد المشاريع (100 مشروع) | [R2] (projects/notegpt) | slug مختصر (`ngpt`) + أدوات إنشاء آلية | T-008, T-010 |
| D-10 | **تأجيل** verify.py وبوابة الأدلة لـ V0.2 | [R8] [R10] (Pre-Flight + Triple Defense) | ⚠️ مؤجل بشرط تفعيل — منع Over-Engineering | T-101 (مؤجلة) |
| D-11 | **تأجيل** handoff + reviews لـ V0.3 | [R11] | ⚠️ مؤجل بشرط تفعيل (3+ أيجنتات) | T-201 (مؤجلة) |
| D-12 | **تأجيل** Branch+PR + tasks/GH-XX لـ V0.4 | [R9] | ⚠️ مؤجل بشرط تفعيل (production) | T-301 (مؤجلة) |
| D-13 | **تأجيل** candidates/ + RELEASES.yaml لـ V0.4 | [R11] | ⚠️ مؤجل بشرط تفعيل | T-302 (مؤجلة) |
| D-14 | **تأجيل** Telegram Orchestrator لـ V0.5 | [R7] [R9] Roadmap | ⚠️ آخر مرحلة | T-401 (مؤجلة) |
| D-15 | `connect-now-lab/` أرشيف قراءة فقط | [CLR] قرار جديد | — | البروتوكول |
| D-16 | مجلد خطة مركزي بنقطة استئناف V3 | طلب زيزو 2026-08-25 | تصميم الملفات الـ 8 | T-P02 |

---

## 2️⃣ ملفات الخطة ← وظيفتها ← مصدر التصميم

| الملف | الوظيفة | مستوحى من |
|---|---|---|
| `V3_RESUME_SESSION.md` | نقطة استئناف رئيسية لأي جلسة | [R5] بند الاستئناف + [MGP] |
| `PROGRESS.md` | الحالة الحية | [R3] progress_*.md |
| `01.25_TASK_LOG.md` | المهام الصغيرة بحالاتها | [R9] tasks isolation (مبسط) |
| `SESSION_LOG.md` | سجل Append-only | [R11] journal/ |
| `TRACEABILITY_MATRIX.md` | ربط القرارات بمصادرها | [R11] Lineage Tracking (موسع) |
| `01.25_MASTER_IMPLEMENTATION_PROMPT.md` | برومبت التكليف الموحد | [MGP] + [R5] |
| `01.25_MULTI_PROJECT_IMPLEMENTATION_PLAN.md` | الخطة والمراحل | [R9] Roadmap + [CLR] |

---

## 3️⃣ مهام V0.1 ← الجولة المصدر

| Task | المصدر |
|---|---|
| T-001 | [R9] الهيكل + [CLR] |
| T-002 | [R9] agents.yaml + [R11] مصفوفة الأكواد |
| T-003 | [R5] البروتوكول (مختصر لصفحة واحدة [CLR]) |
| T-004 | [MGP] + [R5] |
| T-005, T-006 | [R3] الغرف + [R11] هيكل الغرفة (مبسط) |
| T-007, T-008, T-009 | [R7] junior_orchestrator (مفكك لأدوات صغيرة [CLR]) |
| T-010 | [R2] projects/notegpt |
| T-011 | [R2] README |
| T-012 | [R6] معيار "صفر تعارض" + سيناريو التوازي |

---
*آخر تحديث: 2026-08-25 — Claude/Genspark (GSK)*
