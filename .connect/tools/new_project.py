#!/usr/bin/env python3
# Based-on: NONE
"""
new_project.py — إنشاء مشروع جديد بالهيكل القياسي بأمر واحد.

الاستخدام:
    python .connect/tools/new_project.py --slug ngpt --name NoteGPT

ينشئ: projects/{slug}/ بمجلدات scripts/ + har/ + outputs/ + README.md
ويرفض الـ slug المكرر.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "projects"

README_TMPL = """# 📦 {name} (`{slug}`)
> أُنشئ: {date} — بواسطة `new_project.py`

## الهيكل
| المجلد | الغرض |
|---|---|
| `scripts/` | السكربتات — التسمية: `{{NN.NN}}_{{CODE}}_{{slug}}.py` |
| `har/` | ملفات HAR / تسجيلات الشبكة |
| `outputs/` | مخرجات التشغيل (لا ترفع ملفات ضخمة) |

## قواعد
- رقم الإصدار التالي: `python .connect/tools/next_version.py --project {slug}`
- الدستور الكامل: `.connect/PROTOCOL.md`
"""


def main() -> None:
    p = argparse.ArgumentParser(description="إنشاء مشروع جديد")
    p.add_argument("--slug", required=True, help="اسم قصير snake_case (يصبح اسم المجلد)")
    p.add_argument("--name", required=True, help="الاسم الوصفي للمشروع")
    args = p.parse_args()

    slug = args.slug.lower()
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,30}", slug):
        sys.exit(f"❌ slug غير صالح: {slug} — حروف صغيرة/أرقام/شرطة سفلية فقط")

    proj = PROJECTS / slug
    if proj.exists():
        sys.exit(f"❌ المشروع {slug} موجود بالفعل: {proj} — ممنوع التكرار")

    for sub in ("scripts", "har", "outputs"):
        (proj / sub).mkdir(parents=True)
        (proj / sub / ".gitkeep").touch()

    proj_readme = README_TMPL.format(
        name=args.name, slug=slug, date=datetime.date.today().isoformat()
    )
    (proj / "README.md").write_text(proj_readme, encoding="utf-8")

    print(f"✅ تم إنشاء المشروع {slug} ({args.name})")
    print(f"   📁 {proj.relative_to(ROOT)}/ → scripts/ har/ outputs/ README.md")


if __name__ == "__main__":
    main()
