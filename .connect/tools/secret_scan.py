#!/usr/bin/env python3
# Based-on: NONE
"""
secret_scan.py — فحص الريبو عن بيانات حساسة مرفوعة بالخطأ.

الاستخدام:
    python3 .connect/tools/secret_scan.py            # تقرير كامل
    python3 .connect/tools/secret_scan.py --quiet    # سطر واحد (للـ CI)
    python3 .connect/tools/secret_scan.py --path projects/ngpt

exit code:
    0 = نظيف
    1 = وُجدت أسرار

سبب وجود الأداة:
    doctor.py لا يفحص الأسرار إطلاقاً (grep -c "secret\\|token" = 0)،
    فيطبع PASS على ريبو يحتوي كلمات مرور وتوكنات حقيقية.
    راجع: inventory/notegpt/CORRECTIONS_ROUND2.md §4
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# ملفات/مجلدات لا تُفحص
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "env"}
SKIP_SUFFIX = {".har", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip",
               ".pyc", ".ico", ".webp", ".mp4", ".woff", ".woff2"}

# أسطر توثيقية تشرح كيفية الفحص — ليست أسراراً
DOC_LINE_HINTS = ("grep -", "grep_", "rg -", "regex", "pattern",
                  "secret_scan", "أمر التحقق", "أوامر إعادة التحقق")

# قيم لا تُعتبر أسراراً (placeholders مقبولة)
SAFE_VALUES = re.compile(
    r"^(|REPLACE_ME|CHANGE_ME|YOUR_[A-Z_]*|xxx+|TODO|None|null|"
    r"<[^>]*>|\.\.\.|example|test|dummy|placeholder|\*+)$",
    re.IGNORECASE,
)

# قيم اختبارية معلنة عن نفسها — ليست أسراراً حتى لو لم تُطابِق SAFE_VALUES
# بالكامل. مطلوبة لأن حُرّاس تسريب الأسرار **يجب** أن تحقن قيمة اعتماد وهمية
# لتتحقق أنها لا تظهر في السجل؛ ولا يجوز إعفاء مجلد `tests/` بالكامل لأن سراً
# حقيقياً قد يُودَع فيه. المعيار هو دلالة القيمة نفسها، لا موقع الملف.
#
# نطاقات `.test` / `.invalid` / `.example` محجوزة بـ RFC 2606 و RFC 6761
# تحديداً لهذا الغرض، فلا يمكن أن تكون حساباً حقيقياً.
TEST_VALUE_MARKERS = re.compile(
    r"canary|probe|dummy|placeholder|fixture|sample|"
    r"^fake[-_]|[-_]fake|^mock[-_]|[-_]mock|"
    r"\.(?:test|invalid|example|localhost)\b|"
    r"^(?:my|the)?[-_]?secret[-_](?:value|text)$",
    re.IGNORECASE,
)

# القواعد: (المعرّف، الوصف، regex يلتقط القيمة في group 1)
RULES = [
    (
        "HARDCODED_PASSWORD",
        "كلمة مرور مكتوبة حرفياً في الكود",
        re.compile(r"""(?:PASSWORD|PASSWD|PWD)\s*(?::\s*str\s*)?=\s*["']([^"']{3,})["']""", re.I),
    ),
    (
        "HARDCODED_SESSION_TOKEN",
        "توكن جلسة مكتوب حرفياً في الكود",
        re.compile(r"""(?:SESSION_TOKEN|ACCESS_TOKEN|AUTH_TOKEN|USER_TOKEN)\s*(?::\s*str\s*)?=\s*["']([^"']{8,})["']""", re.I),
    ),
    (
        "HARDCODED_EMAIL_CRED",
        "إيميل حساب مكتوب حرفياً (بيانات دخول)",
        re.compile(r"""(?:EMAIL|USERNAME|USER_EMAIL)\s*(?::\s*str\s*)?=\s*["']([^"']*@[^"']+)["']""", re.I),
    ),
    (
        "HARDCODED_API_KEY",
        "مفتاح API مكتوب حرفياً",
        re.compile(r"""(?:API_KEY|APIKEY|SECRET_KEY|CLIENT_SECRET)\s*(?::\s*str\s*)?=\s*["']([^"']{8,})["']""", re.I),
    ),
    (
        "GITHUB_TOKEN_LITERAL",
        "توكن GitHub بصيغته المعروفة",
        re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{16,})\b"),
    ),
    (
        "OPENAI_KEY_LITERAL",
        "مفتاح OpenAI بصيغته المعروفة",
        re.compile(r"\b(sk-[A-Za-z0-9]{20,})\b"),
    ),
    (
        "BEARER_LITERAL",
        "Bearer token مكتوب حرفياً (ليس متغيراً)",
        re.compile(r"""["']Bearer\s+([A-Za-z0-9._\-]{16,})["']"""),
    ),
]

# لو السطر فيه واحد من دول، القيمة جاية من مصدر آمن
SAFE_LINE_HINTS = ("os.environ", "os.getenv", "getenv(", "environ[",
                   "ENV[", "process.env", "load_dotenv", "argparse",
                   "input(", "getpass")

# الأسرار المحقونة في البيئة — عكس اتجاه SAFE_LINE_HINTS.
#
# الجذر: كل الأنماط في SAFE_LINE_HINTS تفترض أن البيئة هي **المصدر**
#     PASSWORD = os.environ["X"]          ← آمن (قراءة)
# لكن نفس الأنماط تظهر حين تكون البيئة هي **الهدف**
#     os.environ["PASSWORD"] = "literal"  ← سرّ مكتوب حرفياً!
# فكان الفحص يقرأ سراً يُحقَن كأنه سرّ يُتجنَّب. القياس المُثبَت: توكن جلسة
# حيّ + إيميل + كلمة مرور في providers/real/notegpt/__main__.py مرّوا بصفر
# تحذيرات لأن السطر يحتوي "os.environ".
#
# القاعدة هنا لا تلتقط إلا الاتجاه الخطر: مفتاح بيئة حسّاس على **يسار** `=`
# وقيمة نصية حرفية على يمينه. القراءة من البيئة لا تطابقها إطلاقاً.
ENV_INJECTION_RULE = (
    "SECRET_INJECTED_INTO_ENV",
    "سرّ مكتوب حرفياً يُحقَن في متغير بيئة",
    re.compile(
        r"""environ(?:\[|\.get\()\s*["'][A-Z0-9_]*"""
        r"""(?:PASSWORD|PASSWD|PWD|TOKEN|SECRET|API_KEY|APIKEY|EMAIL)"""
        r"""[A-Z0-9_]*["']\s*\]?\s*=\s*["']([^"']{3,})["']""",
        re.I,
    ),
)
RULES.append(ENV_INJECTION_RULE)

# قواعد لا يجوز إسكاتها بـ SAFE_LINE_HINTS (لأن الـ hint نفسه جزء من النمط)
DIRECTION_SENSITIVE_RULES = {ENV_INJECTION_RULE[0]}


def is_safe(value: str, line: str, rule_id: str = "") -> bool:
    """هل القيمة الملتقطة آمنة (placeholder أو من متغير بيئة)؟"""
    if SAFE_VALUES.match(value.strip()):
        return True
    # قيمة تُعلن عن نفسها كاختبارية (canary/probe/نطاق محجوز) — تُستثنى في أي
    # ملف، فالمعيار دلالة القيمة لا موقع الملف.
    if TEST_VALUE_MARKERS.search(value.strip()):
        return True
    # قاعدة الحقن تُطابِق سطراً يحتوي "os.environ" بالضرورة، فإسكاتها بـ
    # SAFE_LINE_HINTS يُلغيها بالكامل. الـ placeholders وحدها تُستثنى.
    if rule_id in DIRECTION_SENSITIVE_RULES:
        return False
    if any(h in line for h in SAFE_LINE_HINTS):
        return True
    # قيمة كلها underscore/dash = placeholder
    if re.fullmatch(r"[_\-\s]*", value):
        return True
    return False


def mask(value: str) -> str:
    """إخفاء القيمة في التقرير — لا نطبع السر نفسه."""
    v = value.strip()
    if len(v) <= 6:
        return "*" * len(v)
    return f"{v[:3]}{'*' * min(len(v) - 6, 12)}{v[-3:]}"


def scan_file(path: Path):
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return findings
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        # تجاهل التعليقات التوضيحية في Markdown/Python
        if stripped.startswith("#") and "=" not in stripped:
            continue
        # تجاهل أسطر توثيق أوامر الفحص (تحتوي الـ pattern نفسه لا سراً)
        if any(h in line for h in DOC_LINE_HINTS):
            continue
        for rule_id, desc, pattern in RULES:
            for m in pattern.finditer(line):
                value = m.group(1)
                if is_safe(value, line, rule_id):
                    continue
                findings.append({
                    "file": str(path.relative_to(ROOT)),
                    "line": lineno,
                    "rule": rule_id,
                    "desc": desc,
                    "masked": mask(value),
                })
    return findings


def walk(base: Path):
    for p in base.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_SUFFIX:
            continue
        # لا نفحص الأداة نفسها (فيها الـ regex patterns)
        if p.name == "secret_scan.py":
            continue
        yield p


def main() -> int:
    ap = argparse.ArgumentParser(description="فحص الأسرار المرفوعة في الريبو")
    ap.add_argument("--path", default=".", help="مسار الفحص (نسبي للجذر)")
    ap.add_argument("--quiet", action="store_true", help="سطر نتيجة واحد فقط")
    args = ap.parse_args()

    base = (ROOT / args.path).resolve()
    if not base.exists():
        print(f"❌ المسار غير موجود: {args.path}", file=sys.stderr)
        return 2

    all_findings = []
    for f in walk(base):
        all_findings.extend(scan_file(f))

    if args.quiet:
        if all_findings:
            files = len({f["file"] for f in all_findings})
            print(f"❌ FAIL — {len(all_findings)} سر في {files} ملف")
            return 1
        print("✅ PASS — لا أسرار")
        return 0

    print("=" * 62)
    print("🔐 secret_scan.py — فحص الأسرار المرفوعة")
    print("=" * 62)
    print(f"المسار: {args.path}")

    if not all_findings:
        print("\n✅ PASS — لم يُعثر على أي أسرار.\n")
        return 0

    # تجميع حسب الملف
    by_file = {}
    for f in all_findings:
        by_file.setdefault(f["file"], []).append(f)

    for fname in sorted(by_file):
        print(f"\n📄 {fname}")
        for f in sorted(by_file[fname], key=lambda x: x["line"]):
            print(f"   سطر {f['line']:>5} │ {f['rule']}")
            print(f"              │ {f['desc']}")
            print(f"              │ القيمة (مُخفاة): {f['masked']}")

    # ملخص حسب القاعدة
    by_rule = {}
    for f in all_findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1

    print("\n" + "-" * 62)
    print("الملخص حسب النوع:")
    for rule, count in sorted(by_rule.items(), key=lambda x: -x[1]):
        print(f"   {rule:<28} ×{count}")

    print("-" * 62)
    print(f"❌ FAIL — {len(all_findings)} سر في {len(by_file)} ملف\n")
    print("⚠️  تعديل الملفات لا يكفي — القيم موجودة في تاريخ Git.")
    print("   1) أبطل/غيّر بيانات الدخول على المنصة فوراً (الخطوة الأهم)")
    print("   2) انقل القيم إلى os.environ + أنشئ .env.example")
    print("   3) أضف .env إلى .gitignore")
    print("   4) تنظيف التاريخ (git filter-repo) = قرار المالك\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
