#!/usr/bin/env python3
# Based-on: NONE
"""
next_version.py — حساب رقم الإصدار التالي أوتوماتيك.

الاستخدام:
    python .connect/tools/next_version.py --project ngpt
    → يطبع مثلاً: 01.07

يفحص projects/{slug}/scripts/ عن أسماء بنمط {NN.NN}_{CODE}_{slug}.py
ويطبع (أعلى NN.NN موجود + 0.01). لو المجلد فاضي → 01.00
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERN = re.compile(r"^(\d{2})\.(\d{2})_[A-Z]{2,4}_.+\.py$")


def next_version(scripts_dir: Path) -> str:
    best = None  # (major, minor)
    for f in scripts_dir.iterdir():
        m = PATTERN.match(f.name)
        if m:
            v = (int(m.group(1)), int(m.group(2)))
            if best is None or v > best:
                best = v
    if best is None:
        return "01.00"
    major, minor = best
    minor += 1
    if minor > 99:
        major, minor = major + 1, 0
    return f"{major:02d}.{minor:02d}"


def main() -> None:
    p = argparse.ArgumentParser(description="رقم الإصدار التالي")
    p.add_argument("--project", required=True, help="slug المشروع (مثال: ngpt)")
    args = p.parse_args()

    scripts = ROOT / "projects" / args.project / "scripts"
    if not scripts.is_dir():
        sys.exit(f"❌ غير موجود: {scripts} — أنشئ المشروع أولاً بـ new_project.py")

    print(next_version(scripts))


if __name__ == "__main__":
    main()
