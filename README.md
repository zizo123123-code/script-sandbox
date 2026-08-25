# 🚀 Script Sandbox Hub — منظومة Connect Multi-Agent

مستودع أتمتة السكربتات + **منظومة تعاون متعددة الأيجنتات** تستخدم GitHub نفسه كذاكرة حية مشتركة (**Git-as-Memory Multi-Agent System**).

---

## ⚡ أيجنت جديد؟ ابدأ هنا (دقيقتان)

1. **اقرأ الدستور:** [`.connect/PROTOCOL.md`](./.connect/PROTOCOL.md) — 10 قواعد + الفلو التشغيلي.
2. **اعرف هويتك:** [`.connect/AGENTS.yaml`](./.connect/AGENTS.yaml) — اختصارك وغرفتك.
3. **افحص الإشارات:** `python .connect/tools/pheromone.py scan` — واحجز مهمتك بـ `claim`.
4. **اشتغل → حدّث `PROGRESS.md` بتاعك → `release` → push.**

> **زيزو (المالك)؟** برومبت تكليف أي أيجنت جاهز للنسخ في [`.connect/PROMPT_TEMPLATE.md`](./.connect/PROMPT_TEMPLATE.md)
> والقرارات المعلقة المطلوبة منك في [`connect-plan-claude-genspark/DECISIONS_QUEUE.md`](./connect-plan-claude-genspark/DECISIONS_QUEUE.md)

---

## 🗂️ هيكل المستودع

| المجلد | الغرض |
|---|---|
| [`.connect/`](./.connect/) | 🧠 عقل المنظومة: الدستور + تعريف الأيجنتات + الغرف + الأدوات + لوحة الفيرومونات 🐜 |
| [`connect-plan-claude-genspark/`](./connect-plan-claude-genspark/) | 📋 الخطة المعتمدة + سجل المهام + التقدم + بروتوكول SWARM-DNA 🧬 |
| [`projects/`](./projects/) | 📦 المشاريع بالهيكل القياسي (`scripts/` + `har/` + `outputs/`) |
| [`NOT_EGPT/`](./NOT_EGPT/) | 🤖 NoteGPT Agent Engine v01.05 (المشروع الأصلي — مصيره في DQ-001) |
| [`connect-now-lab/`](./connect-now-lab/) | 📚 أرشيف الجولات المعمارية 1-11 (**قراءة فقط**) |

---

## 🔧 الأدوات (`.connect/tools/`)

```bash
# حجز مهمة قبل الشغل (إلزامي — يمنع سباق المهام)
python .connect/tools/pheromone.py claim --agent AG --target T-007 --ttl 4

# إنشاء أيجنت جديد (غرفة + تحديث AGENTS.yaml)
python .connect/tools/new_agent.py --code GM --name Gemini --role "مراجعة"

# إنشاء مشروع جديد بالهيكل القياسي
python .connect/tools/new_project.py --slug myapp --name "My App"

# رقم الإصدار التالي لسكربت جديد
python .connect/tools/next_version.py --project myapp
```

---

## 🤖 المشروع الأصلي: NOT_EGPT

> **NoteGPT Real Agent Sandbox Engine (v01.05)** — تشغيل Daytona Sandbox بـ Pure Requests،
> Vision، تفريغ YouTube، تدوير IP. [التوثيق الكامل](./NOT_EGPT/)

```bash
cd NOT_EGPT && pip install -r requirements.txt
python 01.05_notegpt_agent_mode.py -p "اكتب مهمتك هنا"
```

---

## 🛡️ قواعد ذهبية مختصرة (التفاصيل في PROTOCOL.md)

- اكتب في غرفتك فقط + ملفات **جديدة** باختصارك — ممنوع تعديل ملفات غيرك.
- `git pull --rebase` قبل أي push — **`--force` محظور**.
- كل commit بـ Trailers: `Agent-Code` / `Task-ID` / `Based-On`.
- التوكن في متغيرات البيئة **فقط** — أي secret في ملف = رفض فوري.

## 📜 License
MIT License
