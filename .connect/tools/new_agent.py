#!/usr/bin/env python3
# Based-on: NONE
"""
new_agent.py — إنشاء غرفة أيجنت جديد + تحديث AGENTS.yaml بأمر واحد.

الاستخدام:
    python .connect/tools/new_agent.py --code GM --name Gemini --role "مراجعة أكواد"

- يرفض الكود المكرر (لو نشط بالفعل).
- لو الكود محجوز (reserved) في AGENTS.yaml → يفعّله.
- ينشئ الغرفة: PROGRESS.md + MEMORY.md + OUTBOX.md + notes/
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # جذر الريبو
CONNECT = ROOT / ".connect"
AGENTS_YAML = CONNECT / "AGENTS.yaml"

PROGRESS_TMPL = """# 📈 PROGRESS.md — غرفة {name} ({code})
## نقطة الاستئناف الشخصية — تُحدَّث قبل كل push (إلزامي)

| البند | القيمة |
|---|---|
| **الحالة** | `IDLE` — لا مهمة جارية |
| **آخر جلسة** | — |
| **آخر Commit** | — |

---

## ✅ آخر إنجاز
- (لا شيء بعد — الغرفة أُنشئت {date})

## 🎯 الخطوة التالية
- في انتظار أول تكليف (راجع `01.25_TASK_LOG.md` أو برومبت زيزو).

## 🚧 المشاكل المعلقة
- لا يوجد.

---
*القالب: الحالة / آخر إنجاز / الخطوة التالية / المشاكل المعلقة — Protocol-Version: 1.0*
"""

MEMORY_TMPL = """# 🧠 MEMORY.md — ذاكرة {name} ({code}) طويلة المدى
## دروس مستفادة + قرارات + معرفة تراكمية (Append-only)

> اكتب هنا أي معرفة تفيد جلساتك القادمة: أنماط نجحت، فخاخ اتجنبها، قرارات معمارية.

---

| التاريخ | الدرس / المعرفة |
|---|---|
| {date} | (الغرفة أُنشئت — لا مدخلات بعد) |
"""

OUTBOX_TMPL = """# 📮 OUTBOX.md — شغل معلق لم يُرفع بعد (غرفة {code})
## قاعدة: فشل push → commit محلي + سطر هنا. أول جلسة تالية: صفِّ هذا الملف أولاً.

| التاريخ | Commit | الوصف | الحالة |
|---|---|---|---|
"""


def load_agents_text() -> str:
    if not AGENTS_YAML.exists():
        sys.exit(f"❌ غير موجود: {AGENTS_YAML} — نفذ T-002 أولاً")
    return AGENTS_YAML.read_text(encoding="utf-8")


def agent_status(text: str, code: str) -> str | None:
    """يرجع status الكود لو موجود في YAML (بدون مكتبات خارجية)."""
    m = re.search(
        rf"^  {re.escape(code)}:\n(?:^    .*\n)*?^    status: (\w+)",
        text,
        re.MULTILINE,
    )
    return m.group(1) if m else None


def main() -> None:
    p = argparse.ArgumentParser(description="إنشاء أيجنت جديد")
    p.add_argument("--code", required=True, help="اختصار الأيجنت (حروف كبيرة، 2-4 حروف)")
    p.add_argument("--name", required=True, help="اسم الأيجنت")
    p.add_argument("--role", required=True, help="وصف الدور")
    args = p.parse_args()

    code = args.code.upper()
    if not re.fullmatch(r"[A-Z]{2,4}", code):
        sys.exit(f"❌ كود غير صالح: {code} — لازم 2-4 حروف لاتينية كبيرة")

    today = datetime.date.today().isoformat()
    room = CONNECT / "agents" / code
    text = load_agents_text()
    status = agent_status(text, code)

    if status == "active":
        sys.exit(f"❌ الكود {code} نشط بالفعل في AGENTS.yaml — ممنوع التكرار")
    if room.exists() and any(room.iterdir()):
        sys.exit(f"❌ الغرفة {room} موجودة وغير فارغة — ممنوع الدهس")

    # --- تحديث AGENTS.yaml ---
    entry = (
        f"  {code}:\n"
        f"    name: {args.name}\n"
        f"    status: active\n"
        f'    role: "{args.role}"\n'
        f'    room: ".connect/agents/{code}/"\n'
        f"    previous_codes: []\n"
        f'    joined: "{today}"\n'
    )
    if status == "reserved":
        # استبدال البلوك المحجوز بالكامل
        pattern = rf"^  {re.escape(code)}:\n(?:^    .*\n)*"
        text = re.sub(pattern, entry, text, count=1, flags=re.MULTILINE)
    else:
        # إضافة تحت agents: مباشرة
        text = re.sub(r"^agents:\n", f"agents:\n{entry}\n", text, count=1, flags=re.MULTILINE)
    AGENTS_YAML.write_text(text, encoding="utf-8")

    # --- إنشاء الغرفة ---
    (room / "notes").mkdir(parents=True, exist_ok=True)
    (room / "notes" / ".gitkeep").touch()
    ctx = {"name": args.name, "code": code, "date": today}
    (room / "PROGRESS.md").write_text(PROGRESS_TMPL.format(**ctx), encoding="utf-8")
    (room / "MEMORY.md").write_text(MEMORY_TMPL.format(**ctx), encoding="utf-8")
    (room / "OUTBOX.md").write_text(OUTBOX_TMPL.format(**ctx), encoding="utf-8")

    print(f"✅ تم إنشاء الأيجنت {code} ({args.name})")
    print(f"   📁 الغرفة: {room.relative_to(ROOT)}")
    print(f"   📝 AGENTS.yaml محدث (status: active)")


if __name__ == "__main__":
    main()
