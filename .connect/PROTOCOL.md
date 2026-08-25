Protocol-Version: 1.0

# 📜 PROTOCOL.md — دستور منظومة Connect Multi-Agent

> **قاعدة النسخة:** لو `protocol_version` في `AGENTS.yaml` مختلف عن أول سطر هنا → أعد قراءة هذا الملف كاملاً قبل أي شغل.

---

## ⚡ الفلو التشغيلي (كل جلسة — بالترتيب)

1. `git pull --rebase origin main`
2. اقرأ غرفتك: `.connect/agents/{CODE}/PROGRESS.md` → خد نقطة الاستئناف.
3. `python .connect/tools/pheromone.py scan` → شوف الإشارات السارية.
4. **احجز مهمتك:** `pheromone.py claim --agent {CODE} --target {TASK} --ttl 4` — ممنوع الشغل بدون CLAIM سارٍ باسمك.
5. نفذ المهمة داخل حدودك (القواعد تحت).
6. حدّث `PROGRESS.md` بتاعك (إلزامي) + حرر الحجز `pheromone.py release`.
7. `git pull --rebase` → commit بالـ Trailers → `git push origin main`.

---

## 🛡️ القواعد الذهبية (10)

1. **حدود الكتابة:** اكتب في غرفتك فقط + ملفات **جديدة** في `projects/*/scripts/` باختصارك. ممنوع تعديل ملف عليه اختصار أيجنت آخر.
2. **التسمية:** `{NN.NN}_{CODE}_{slug}.py` — الرقم من `next_version.py`. أول سطر: `# Based-on: <الأصل أو NONE>`.
3. **Git:** `pull --rebase` قبل أي push. **`--force` محظور نهائياً.**
4. **Trailers إلزامية في كل commit:**
   ```
   Agent-Code: {CODE}
   Task-ID: {T-XXX}
   Based-On: {ملف الأصل أو NONE}
   ```
5. **الاستئناف:** جلسة بدون تحديث `PROGRESS.md` = جلسة فاشلة.
6. **لا Over-Engineering:** ممنوع تنفيذ مهام مرحلة لم يتحقق شرط تفعيلها (راجع الخطة).
7. **🔐 الأسرار:** التوكن في متغيرات البيئة **فقط** (`$GITHUB_TOKEN`). أي ملف يحتوي secret = رفض فوري + حذف.
8. **🐜 الحجز أولاً:** ممنوع بدء مهمة بدون فيرومون `CLAIM` سارٍ باسمك. لقيت CLAIM سارٍ لغيرك على المهمة؟ خد مهمة تانية.
9. **🚑 التعافي:** الخطأ على main يتصلح بـ `git revert` **فقط** (ممنوع reset/rebase على تاريخ مدفوع) + وثّق الحادث في غرفتك + فيرومون `WARN`.
10. **📮 العمل المنقطع:** فشل الـ push؟ Commit محلي دايماً + سجل السطر في `.connect/agents/{CODE}/OUTBOX.md` — الشغل ما يضيعش. أول جلسة تالية: صفّي الـ OUTBOX أولاً.

---

## 🐜 الفيرومونات (المرجع الكامل: `connect-plan-claude-genspark/02.00_SWARM_DNA_PROTOCOL.md`)

| النوع | المعنى | مثال |
|---|---|---|
| `CLAIM` | حجز مهمة (بـ TTL بالساعات) | `CLAIM_AG_t007.yaml` |
| `WARN` | تحذير من مسار/ملف به مشكلة | `WARN_DS_flaky_api.yaml` |
| `TRAIL` | مسار ناجح يُنصح باتباعه | `TRAIL_AG_auth_flow.yaml` |
| `NEED` | مطلوب قرار/مورد من زيزو | `NEED_GSK_dq001.yaml` |

- الأوامر: `claim / release / scan / sweep` — عبر `.connect/tools/pheromone.py`.
- إشارة منتهية الـ TTL = هالكة، أي أيجنت يكنسها بـ `sweep`.

---

## 🗳️ قرارات زيزو

أي قرار مطلوب من المالك → سطر جديد في `connect-plan-claude-genspark/DECISIONS_QUEUE.md` + فيرومون `NEED`. ممنوع تخمين رد زيزو أو تنفيذ الأمر المعلق.

---

## 🗂️ خريطة سريعة

| عايز إيه؟ | فين؟ |
|---|---|
| تعريف الأيجنتات | `.connect/AGENTS.yaml` |
| غرفتك (استئناف/ذاكرة) | `.connect/agents/{CODE}/` |
| الأدوات | `.connect/tools/` |
| الإشارات | `.connect/pheromones/` |
| برومبت التكليف | `.connect/PROMPT_TEMPLATE.md` |
| الخطة والمهام | `connect-plan-claude-genspark/` |
| قرارات زيزو المعلقة | `connect-plan-claude-genspark/DECISIONS_QUEUE.md` |

---
*Protocol-Version: 1.0 — أي تعديل جوهري يرفع النسخة ويحدث `AGENTS.yaml`.*
