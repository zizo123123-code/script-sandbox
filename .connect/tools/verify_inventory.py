#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_inventory.py — بوابة التحقق الآلي لملفات inventory/<provider>/

الغرض: منع تكرار كارثة inventory/notegpt — ملفات موسومة CONFIRMED
بأدلة غير قابلة للتتبع (نماذج وهمية، endpoints مختلقة، أرقام سطور مغلوطة).

يفحص آلياً:
  1. النماذج المذكورة في models.md موجودة فعلاً في notegpt_catalog.json
  2. الـ endpoints المذكورة موجودة فعلاً في الكود أو الـ HAR
  3. أرقام السطور المرجعية داخل حدود الملف المُشار إليه
  4. كل CONFIRMED عنده سطر Evidence/دليل
  5. وجود الملفات الـ 11 المعيارية (§15)

الاستخدام:
    python3 .connect/tools/verify_inventory.py                 # كل المزودين
    python3 .connect/tools/verify_inventory.py --provider ngpt # مزود واحد
    python3 .connect/tools/verify_inventory.py --strict         # التحذيرات تفشل أيضاً
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import io
from pathlib import Path

# تأمين مخرجات UTF-8 على كافة الأنظمة
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "inventory"

# الملفات المعيارية الـ 11 حسب §15 من الدستور
REQUIRED_FILES = [
    "account.md", "models.md", "capabilities.md", "generation.md",
    "upload.md", "limits.md", "errors.md", "health.md",
    "notes.md", "agent.md", "provider_summary.md",
]

# ربط مجلد الـ inventory بمشروع الكود المقابل
PROVIDER_MAP = {
    "notegpt": {
        "project": "projects/ngpt",
        "catalog": "notegpt_catalog.json",
        "code_glob": "scripts/*.py",
        "har_glob": "har/*.har",
    },
}

C_RED, C_YEL, C_GRN, C_CYN, C_DIM, C_RST = (
    "\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[2m", "\033[0m"
)

errors: list[str] = []
warns: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)
    print(f"{C_RED}  ❌ {msg}{C_RST}")


def warn(msg: str) -> None:
    warns.append(msg)
    print(f"{C_YEL}  ⚠️  {msg}{C_RST}")


def ok(msg: str) -> None:
    print(f"{C_GRN}  ✅ {msg}{C_RST}")


def head(msg: str) -> None:
    print(f"\n{C_CYN}{'=' * 62}\n{msg}\n{'=' * 62}{C_RST}")


# ─────────────────────────────────────────────────────────────
# 1. الملفات المعيارية
# ─────────────────────────────────────────────────────────────
def check_required_files(pdir: Path) -> None:
    print(f"\n{C_DIM}[1/5] الملفات المعيارية (§15){C_RST}")
    missing = [f for f in REQUIRED_FILES if not (pdir / f).exists()]
    if missing:
        err(f"ملفات مفقودة: {', '.join(missing)}")
    else:
        ok(f"الـ {len(REQUIRED_FILES)} ملفاً المعياري موجودة")

    extra = sorted(
        p.name for p in pdir.glob("*.md")
        if p.name not in REQUIRED_FILES and p.name != "CORRECTIONS.md"
    )
    if extra:
        print(f"{C_DIM}     ملفات إضافية (مسموحة §15): {', '.join(extra)}{C_RST}")


# ─────────────────────────────────────────────────────────────
# 2. النماذج مقابل الكاتالوج
# ─────────────────────────────────────────────────────────────
def check_models(pdir: Path, proj: Path, catalog_name: str) -> None:
    print(f"\n{C_DIM}[2/5] النماذج مقابل الكاتالوج{C_RST}")
    md = pdir / "models.md"
    cat = proj / catalog_name
    if not md.exists():
        return
    if not cat.exists():
        warn(f"الكاتالوج غير موجود ({catalog_name}) — تخطي فحص النماذج")
        return

    try:
        data = json.loads(cat.read_text(encoding="utf-8"))
    except Exception as ex:  # noqa: BLE001
        err(f"فشل قراءة الكاتالوج: {type(ex).__name__}: {ex}")
        return

    entries = data if isinstance(data, list) else data.get("models", [])
    real = {}
    for m in entries:
        if isinstance(m, dict):
            mid = m.get("model") or m.get("id") or m.get("name")
            if mid:
                real[mid] = m

    text = md.read_text(encoding="utf-8")
    claimed = {m.strip() for m in re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`", text, re.M)}

    ghosts = sorted(claimed - set(real))
    for g in ghosts:
        err(f"models.md: نموذج وهمي غير موجود في الكاتالوج → `{g}`")

    undocumented = sorted(set(real) - claimed)
    for u in undocumented:
        warn(f"models.md: نموذج حقيقي غير موثق → `{u}`")

    # التحقق من الأزمنة المعلنة
    for mid, rest in re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`\s*\|(.*)$", text, re.M):
        mid = mid.strip()
        if mid not in real:
            continue
        m = re.search(r"([\d.]+)\s*s\b", rest)
        actual = real[mid].get("dur")
        if m and actual is not None and abs(float(m.group(1)) - float(actual)) > 0.001:
            err(f"models.md: زمن `{mid}` مُعلن {m.group(1)}s والحقيقي {actual}s")

    # التحقق من العدد المعلن في الترويسة
    declared = re.search(r"(\d+)\s*نموذج", text)
    if declared and int(declared.group(1)) != len(real):
        err(f"models.md: يعلن {declared.group(1)} نموذجاً والكاتالوج فيه {len(real)}")

    if not ghosts and not undocumented:
        ok(f"كل النماذج ({len(real)}) مطابقة للكاتالوج")


# ─────────────────────────────────────────────────────────────
# 3. الـ endpoints مقابل الكود والـ HAR
# ─────────────────────────────────────────────────────────────
def collect_real_endpoints(proj: Path, code_glob: str, har_glob: str) -> set[str]:
    found: set[str] = set()
    for f in proj.glob(code_glob):
        try:
            for m in re.findall(r"/api/v\d+/[A-Za-z0-9/_\-]+", f.read_text(
                    encoding="utf-8", errors="replace")):
                found.add(m.rstrip("/"))
        except Exception:  # noqa: BLE001, S110
            pass
    for f in proj.glob(har_glob):
        try:
            har = json.loads(f.read_text(encoding="utf-8", errors="replace"))
            for e in har.get("log", {}).get("entries", []):
                m = re.search(r"/api/v\d+/[A-Za-z0-9/_\-]+",
                              e.get("request", {}).get("url", ""))
                if m:
                    found.add(m.group(0).rstrip("/"))
        except Exception:  # noqa: BLE001, S110
            pass
    return found


def check_endpoints(pdir: Path, proj: Path, code_glob: str, har_glob: str) -> None:
    print(f"\n{C_DIM}[3/5] الـ endpoints مقابل الكود/HAR{C_RST}")
    real = collect_real_endpoints(proj, code_glob, har_glob)
    if not real:
        warn("لم يُعثر على أي endpoint في الكود أو الـ HAR — تخطي")
        return

    bad = 0
    for md in sorted(pdir.glob("*.md")):
        if md.name == "CORRECTIONS.md":
            continue
        for ep in set(re.findall(r"/api/v\d+/[A-Za-z0-9/_\-]+",
                                 md.read_text(encoding="utf-8"))):
            ep = ep.rstrip("/")
            if ep not in real:
                err(f"{md.name}: endpoint غير موجود في الكود/HAR → {ep}")
                bad += 1
    if not bad:
        ok(f"كل الـ endpoints المذكورة موجودة فعلاً ({len(real)} مرصود)")


# ─────────────────────────────────────────────────────────────
# 4. أرقام السطور المرجعية
# ─────────────────────────────────────────────────────────────
def check_line_refs(pdir: Path, proj: Path) -> None:
    print(f"\n{C_DIM}[4/5] أرقام السطور المرجعية{C_RST}")
    cache: dict[str, int] = {}
    bad = 0
    checked = 0

    for md in sorted(pdir.glob("*.md")):
        if md.name == "CORRECTIONS.md":
            continue
        text = md.read_text(encoding="utf-8")
        # يمسك: `01.05` سطر 240-310  /  01.05:806  /  `01.05` سطر 518
        pats = [
            r"`?(\d{2}\.\d{2})`?\s*(?:سطر|line)\s*(\d+)(?:\s*[-–]\s*(\d+))?",
            r"`?(\d{2}\.\d{2})`?[_a-z]*\.py:(\d+)",
            r"`(\d{2}\.\d{2}):(\d+)`",
        ]
        for pat in pats:
            for m in re.finditer(pat, text):
                ver = m.group(1)
                a = int(m.group(2))
                b = m.group(3) if (m.lastindex and m.lastindex >= 3) else None
                if ver not in cache:
                    hits = list(proj.glob(f"scripts/{ver}*.py"))
                    cache[ver] = (
                        len(hits[0].read_text(encoding="utf-8",
                                              errors="replace").splitlines())
                        if hits else -1
                    )
                total = cache[ver]
                if total < 0:
                    warn(f"{md.name}: سكربت الإصدار {ver} غير موجود")
                    continue
                checked += 1
                hi = int(b) if b else a
                if a < 1 or hi > total:
                    err(f"{md.name}: مرجع سطر خارج الحدود → {ver} سطر {a}"
                        f"{'-' + b if b else ''} (الملف {total} سطراً)")
                    bad += 1

    if checked == 0:
        warn("لا توجد مراجع سطور — الأدلة غير قابلة للتتبع (§14)")
    elif not bad:
        ok(f"كل مراجع السطور ({checked}) داخل الحدود")
    print(f"{C_DIM}     ملاحظة: الفحص يتأكد من الحدود فقط، لا من صحة المحتوى{C_RST}")


# ─────────────────────────────────────────────────────────────
# 5. كل CONFIRMED عنده دليل
# ─────────────────────────────────────────────────────────────
EVIDENCE_HINT = re.compile(
    r"سطر|line|Evidence|الدليل|HAR|:\d+|\.py|\.json|entry", re.I
)


def check_evidence(pdir: Path) -> None:
    print(f"\n{C_DIM}[5/5] الأدلة مقابل وسوم CONFIRMED (§14){C_RST}")
    bare = 0
    total = 0
    for md in sorted(pdir.glob("*.md")):
        if md.name == "CORRECTIONS.md":
            continue
        for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if "CONFIRMED" not in line or "UNSUPPORTED" in line:
                continue
            if not line.lstrip().startswith("|"):
                continue
            total += 1
            if not EVIDENCE_HINT.search(line):
                warn(f"{md.name}:{i} — CONFIRMED بلا دليل قابل للتتبع")
                bare += 1
    if total == 0:
        print(f"{C_DIM}     لا توجد صفوف CONFIRMED في جداول{C_RST}")
    elif not bare:
        ok(f"كل صفوف CONFIRMED ({total}) عندها إشارة دليل")


# ─────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="بوابة التحقق لملفات inventory/")
    ap.add_argument("--provider", help="اسم مجلد المزود (مثال: notegpt)")
    ap.add_argument("--strict", action="store_true",
                    help="اجعل التحذيرات تُفشل الفحص")
    args = ap.parse_args()

    if not INVENTORY.exists():
        print(f"{C_YEL}لا يوجد مجلد inventory/ — لا شيء للفحص{C_RST}")
        return 0

    providers = (
        [INVENTORY / args.provider] if args.provider
        else sorted(p for p in INVENTORY.iterdir() if p.is_dir())
    )

    for pdir in providers:
        if not pdir.exists():
            print(f"{C_RED}المزود غير موجود: {pdir}{C_RST}")
            return 2
        head(f"🔎 فحص المزود: {pdir.name}")
        cfg = PROVIDER_MAP.get(pdir.name)
        check_required_files(pdir)
        if cfg:
            proj = ROOT / cfg["project"]
            check_models(pdir, proj, cfg["catalog"])
            check_endpoints(pdir, proj, cfg["code_glob"], cfg["har_glob"])
            check_line_refs(pdir, proj)
        else:
            warn(f"لا يوجد PROVIDER_MAP لـ '{pdir.name}' — "
                 f"تخطي فحوص النماذج/الـ endpoints/السطور")
        check_evidence(pdir)

    head("النتيجة النهائية")
    print(f"  أخطاء: {len(errors)}   |   تحذيرات: {len(warns)}")
    failed = bool(errors) or (args.strict and bool(warns))
    if failed:
        print(f"{C_RED}❌ VERIFIED_FAIL — لا يجوز اعتماد الـ Inventory كمرجع{C_RST}")
        return 1
    print(f"{C_GRN}✅ VERIFIED_PASS{C_RST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
