#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rewrite_secrets.py — إعادة كتابة الأسرار المكتوبة حرفياً إلى os.environ.get()

الهدف: الحفاظ على الأرشيف المرجعي في projects/ngpt/ عاملاً ومقروءاً،
مع نقل القيم الحسّاسة إلى متغيرات بيئة + placeholders.

مبادئ التصميم (مستخلصة من قياس فعلي، لا من افتراض):

1) الاستهداف بالـ AST لا بالـ regex.
   المحرك يحلّل الشجرة ويطابق إسنادات الأسماء الحسّاسة التي قيمتها
   سلسلة حرفية غير فارغة. سبب ذلك مقيس: الملف
   test_deepseek_vs_minimax_agent_duel.py يحتوي SESSION_TOKEN: str = ""
   وهي *ليست* سرّاً. regex على الاسم وحده كان سيعدّها 30 بدل 29.

2) لا نلمس القيم الفارغة ولا القيم غير الحرفية.
   السلسلة الفارغة سلوك مقصود (تعطيل التوكن)، وتغييرها يغيّر المنطق.

3) الاستبدال يحافظ على التعليم النوعي (annotation).
   الصيغة في الأرشيف هي `EMAIL: str = "..."` داخل dataclass-like Config،
   وحذف `: str` قد يغيّر دلالة الصنف. لذا نُبقي التعليم كما هو.

4) الافتراضي (default) يبقى سلسلة فارغة وليس placeholder وهمياً.
   لأن الكود الأصلي يفحص `if not Config.EMAIL or not Config.PASSWORD`
   ثم يتخطّى تسجيل الدخول. لو وضعنا "YOUR_EMAIL_HERE" كافتراضي،
   لصار الفحص يمرّ بقيمة كاذبة وحاول الكود تسجيل دخول بقيمة وهمية —
   أي أننا نكسر الأرشيف بصمت. السلسلة الفارغة تحفظ السلوك الأصلي.

الاستخدام:
    python .connect/tools/rewrite_secrets.py --check   # تقرير بلا تعديل
    python .connect/tools/rewrite_secrets.py --apply   # تنفيذ
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import re
import sys
from pathlib import Path

# الجذر: نطاق العمل محصور في الأرشيف المرجعي فقط.
REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = REPO_ROOT / "projects" / "ngpt"

# الأسماء الحسّاسة -> اسم متغير البيئة المقابل.
# ملاحظة: القيمة هنا هي *اسم* متغير بيئة، لا سرّ.
SECRET_NAMES: dict[str, str] = {
    "EMAIL": "NOTEGPT_EMAIL",
    "PASSWORD": "NOTEGPT_PASSWORD",
    "SESSION_TOKEN": "NOTEGPT_SESSION_TOKEN",
}


class Finding:
    """موضع سرّ حرفي واحد داخل ملف."""

    __slots__ = ("path", "lineno", "col", "end_col", "name", "env", "raw_len", "annotated")

    def __init__(self, path, lineno, col, end_col, name, env, raw_len, annotated):
        self.path = path
        self.lineno = lineno
        self.col = col
        self.end_col = end_col
        self.name = name
        self.env = env
        self.raw_len = raw_len
        self.annotated = annotated

    def __repr__(self) -> str:  # pragma: no cover - تشخيصي فقط
        return f"<Finding {self.path.name}:{self.lineno} {self.name}>"


def _target_name(node: ast.AST) -> str | None:
    """يستخرج اسم الهدف من إسناد عادي أو مُعلَّم."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def find_secrets(path: Path) -> list[Finding]:
    """يحلّل ملفاً ويعيد مواضع الأسرار الحرفية غير الفارغة."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # ملف غير قابل للتحليل: نتجاهله بصراحة بدل تعديله بـ regex أعمى.
        return []

    out: list[Finding] = []
    for node in ast.walk(tree):
        # نغطّي الصيغتين: EMAIL = "..."  و  EMAIL: str = "..."
        if isinstance(node, ast.AnnAssign):
            targets, annotated = [node.target], True
        elif isinstance(node, ast.Assign):
            targets, annotated = node.targets, False
        else:
            continue

        value = node.value
        if value is None:
            continue
        # شرط 1: القيمة سلسلة حرفية.
        if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
            continue
        # شرط 2: غير فارغة — السلسلة الفارغة ليست سرّاً (مقيس).
        if value.value == "":
            continue

        for tgt in targets:
            name = _target_name(tgt)
            if name in SECRET_NAMES:
                out.append(
                    Finding(
                        path=path,
                        lineno=value.lineno,
                        col=value.col_offset,
                        end_col=value.end_col_offset,
                        name=name,
                        env=SECRET_NAMES[name],
                        raw_len=len(value.value),
                        annotated=annotated,
                    )
                )
    return out


def ensure_os_import(source: str) -> tuple[str, bool]:
    """يضمن وجود `import os`. يعيد (المصدر, هل أُضيف)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, False

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(a.name == "os" or a.name.startswith("os.") for a in node.names):
                return source, False
        elif isinstance(node, ast.ImportFrom):
            if node.module == "os":
                return source, False

    lines = source.splitlines(keepends=True)
    # نُدرج بعد docstring الوحدة إن وُجد، وإلا بعد أسطر الترميز/الشيبانغ.
    insert_at = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(
        getattr(tree.body[0], "value", None), ast.Constant
    ) and isinstance(tree.body[0].value.value, str):
        insert_at = tree.body[0].end_lineno
    else:
        for i, line in enumerate(lines[:3]):
            if line.startswith("#!") or "coding" in line:
                insert_at = i + 1
    lines.insert(insert_at, "import os\n")
    return "".join(lines), True


def rewrite_file(path: Path, findings: list[Finding]) -> str:
    """يبني نص الملف بعد الاستبدال. لا يكتب على القرص."""
    source = path.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)

    # نعمل من الأسفل للأعلى حتى لا تتزحزح المواضع بعد كل استبدال.
    for f in sorted(findings, key=lambda x: (x.lineno, x.col), reverse=True):
        idx = f.lineno - 1
        line = lines[idx]
        # الافتراضي "" مقصود: يحفظ فحص `if not Config.EMAIL` الأصلي.
        replacement = f'os.environ.get("{f.env}", "")'
        lines[idx] = line[: f.col] + replacement + line[f.end_col :]

    new_source = "".join(lines)
    new_source, _ = ensure_os_import(new_source)
    return new_source


def iter_py_files(root: Path):
    """يمرّ على ملفات .py — rglob يتعامل مع المسافات في الأسماء بأمان."""
    yield from sorted(root.rglob("*.py"))


def main() -> int:
    ap = argparse.ArgumentParser(description="إعادة كتابة الأسرار إلى os.environ")
    ap.add_argument("--apply", action="store_true", help="تنفيذ التعديل فعلياً")
    ap.add_argument("--check", action="store_true", help="تقرير بلا تعديل")
    args = ap.parse_args()

    if not args.apply and not args.check:
        ap.error("اختر --check أو --apply")

    if not TARGET_DIR.is_dir():
        print(f"❌ المجلد غير موجود: {TARGET_DIR}")
        return 2

    total = 0
    touched = 0
    print(f"النطاق: {TARGET_DIR.relative_to(REPO_ROOT)}")
    print("-" * 62)

    for path in iter_py_files(TARGET_DIR):
        findings = find_secrets(path)
        if not findings:
            continue
        touched += 1
        total += len(findings)
        rel = path.relative_to(REPO_ROOT)
        print(f"📄 {rel}  ({len(findings)} سر)")
        for f in sorted(findings, key=lambda x: x.lineno):
            print(f"    سطر {f.lineno:>4} │ {f.name:<14} → os.environ.get(\"{f.env}\", \"\")")

        if args.apply:
            new_source = rewrite_file(path, findings)
            # حاجز أمان: الناتج يجب أن يبقى Python صحيحاً.
            try:
                ast.parse(new_source)
            except SyntaxError as exc:
                print(f"    ❌ رُفض: الناتج غير صحيح نحوياً ({exc}) — لم يُكتب")
                return 1
            path.write_text(new_source, encoding="utf-8")

    print("-" * 62)
    verb = "استُبدل" if args.apply else "سيُستبدل"
    print(f"{verb}: {total} سر في {touched} ملف")
    return 0


if __name__ == "__main__":
    sys.exit(main())
