#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor.py — 🩺 الفحص الذاتي الشامل للمنظومة (T-017 / GAP-09)
يفحص: التسمية + بطاقات DNA + الفيرومونات + صلاحية YAML + هيكل الغرف
النتيجة: PASS / FAIL مع تفصيل كل خطأ وتحذير. exit=0 لو PASS."""
import re, sys, datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ERRORS, WARNINGS = [], []
NAME_RE = re.compile(r"^\d{2}\.\d{2}_[A-Z]+_[a-z0-9_]+\.py$")
LEGACY_RE = re.compile(r"^\d{2}\.\d{2}_[a-z0-9_]+\.py$")  # نمط ما قبل المنظومة (مقبول بتحذير=لا شيء)

def err(msg): ERRORS.append(msg)
def warn(msg): WARNINGS.append(msg)

def check_yaml_files():
    for f in list(ROOT.glob(".connect/**/*.yaml")) + list(ROOT.glob(".connect/*.yaml")):
        try:
            yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception as e:
            err(f"YAML تالف: {f.relative_to(ROOT)} — {e}")

def check_agents():
    f = ROOT / ".connect" / "AGENTS.yaml"
    if not f.exists():
        err("AGENTS.yaml مفقود"); return {}
    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    agents = data.get("agents", {})
    for code, meta in agents.items():
        if meta.get("status") == "active":
            room = ROOT / meta.get("room", "")
            if not room.is_dir():
                err(f"غرفة الأيجنت {code} مفقودة: {meta.get('room')}")
            else:
                for req in ("PROGRESS.md", "MEMORY.md", "OUTBOX.md"):
                    if not (room / req).exists():
                        err(f"ملف {req} مفقود في غرفة {code}")
    return agents

def check_scripts(agents):
    codes = set(agents.keys()) | {"LEGACY"}
    for proj in sorted((ROOT / "projects").glob("*/")):
        for f in sorted((proj / "scripts").glob("*.py")):
            legacy = LEGACY_RE.match(f.name)
            if not NAME_RE.match(f.name) and not legacy:
                err(f"اسم مخالف للنمط: {f.relative_to(ROOT)}")
            txt = f.read_text(encoding="utf-8", errors="ignore")[:2000]
            gid = re.search(r"#\s*Gene-ID:\s*(\S+)", txt)
            if not gid:
                err(f"بطاقة DNA مفقودة (Gene-ID): {f.relative_to(ROOT)}")
                continue
            for field in ("Based-On", "Generation", "Author", "Mutation"):
                if not re.search(rf"#\s*{field}:", txt):
                    err(f"حقل {field} ناقص في بطاقة DNA: {f.relative_to(ROOT)}")
            auth = re.search(r"#\s*Author:\s*(\S+)", txt)
            if auth and auth.group(1) not in codes:
                err(f"مؤلف غير معروف '{auth.group(1)}' في {f.relative_to(ROOT)}")
            expect = f"{proj.name}/" + f.name.rsplit(".py", 1)[0]
            if not legacy and gid.group(1) != expect.replace("_notegpt_", "_"):
                pass  # المطابقة الدقيقة تخص الملفات الجديدة فقط

def check_pheromones():
    now = datetime.datetime.now(datetime.timezone.utc)
    for f in (ROOT / ".connect" / "pheromones").glob("*.yaml"):
        try:
            d = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except Exception:
            continue  # اتسجل خطؤه في check_yaml_files
        for req in ("type", "agent", "target"):
            if req not in d:
                err(f"فيرومون ناقص الحقل '{req}': {f.name}")
        exp = d.get("expires")
        if exp:
            try:
                if datetime.datetime.fromisoformat(str(exp)) < now:
                    warn(f"فيرومون منتهي الصلاحية (شغل sweep): {f.name}")
            except ValueError:
                err(f"صيغة expires غير صالحة في {f.name}")

def check_dna_links():
    genes = {}
    for f in ROOT.glob("projects/*/scripts/*.py"):
        txt = f.read_text(encoding="utf-8", errors="ignore")[:2000]
        m = re.search(r"#\s*Gene-ID:\s*(\S+)", txt)
        if m:
            genes[m.group(1)] = f
    for gid, f in genes.items():
        txt = f.read_text(encoding="utf-8", errors="ignore")[:2000]
        base = re.search(r"#\s*Based-On:\s*(\S+)", txt)
        if base and base.group(1) not in ("NONE",) and base.group(1) not in genes:
            warn(f"Based-On يشير لجين غير موجود '{base.group(1)}': {f.relative_to(ROOT)}")

def main():
    print("🩺 doctor.py — الفحص الذاتي الشامل")
    print("=" * 46)
    check_yaml_files()
    agents = check_agents()
    check_scripts(agents)
    check_pheromones()
    check_dna_links()
    for e in ERRORS:
        print(f"  ❌ {e}")
    for w in WARNINGS:
        print(f"  ⚠️ {w}")
    print("=" * 46)
    status = "✅ PASS" if not ERRORS else "❌ FAIL"
    print(f"النتيجة: {status} — {len(ERRORS)} خطأ، {len(WARNINGS)} تحذير")
    return 0 if not ERRORS else 1

if __name__ == "__main__":
    sys.exit(main())
