#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""trust_ledger.py — 🏆 سجل الثقة (الركن 3 من SWARM-DNA)
يحسب سمعة الأيجنتات آلياً من مصدرين ويولد .connect/TRUST_LEDGER.md:
  1. .connect/TRUST_EVENTS.yaml — سجل أحداث دائم (append-only).
     ⚠️ هذا هو المصدر الأساسي لأن مزامنة المنصة تعيد كتابة رسائل commits
     فتمسح الـ Trailers — الأحداث هنا تنجو من أي إعادة كتابة.
  2. Git Trailers (Agent-Code/Task-ID) — تُقرأ إن وُجدت (dedup بالمهمة).
  3. بطاقات DNA — أي سكربت بُني عليه من أيجنت آخر يمنح مؤلفه +15.
Deterministic: نفس المدخلات → نفس الأرقام دائماً."""
import re, subprocess, sys, datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
EVENTS_FILE = ROOT / ".connect" / "TRUST_EVENTS.yaml"
OUT = ROOT / ".connect" / "TRUST_LEDGER.md"
RANKS = [(150, "👑 Queen's Guard"), (70, "🥇 Architect"), (30, "🥈 Builder"), (0, "🐜 Scout")]

def rank_of(pts):
    for th, name in RANKS:
        if pts >= th:
            return name
    return "🐜 Scout"

def load_events():
    """أحداث دائمة: [{agent, points, task, note, date}]"""
    if not EVENTS_FILE.exists():
        return []
    data = yaml.safe_load(EVENTS_FILE.read_text(encoding="utf-8")) or {}
    return data.get("events", [])

def git_trailer_events(seen_tasks):
    """+10 لكل commit فيه Agent-Code + Task-ID (لو المهمة مش متسجلة في الأحداث)."""
    try:
        log = subprocess.run(["git", "log", "--format=%h%x00%b%x01"],
                             capture_output=True, text=True, cwd=ROOT, check=True).stdout
    except Exception:
        return []
    out = []
    for chunk in log.split("\x01"):
        if "\x00" not in chunk:
            continue
        h, body = chunk.split("\x00", 1)
        ac = re.search(r"^Agent-Code:\s*(\S+)", body, re.M)
        ti = re.search(r"^Task-ID:\s*(\S+)", body, re.M)
        if ac and ti and (ac.group(1), ti.group(1)) not in seen_tasks:
            seen_tasks.add((ac.group(1), ti.group(1)))
            out.append({"agent": ac.group(1), "points": 10,
                        "note": f"مهمة {ti.group(1)} ({h.strip()})"})
    return list(reversed(out))

def dna_buildon_events():
    """+15 لمؤلف أي جين بنى عليه أيجنت آخر."""
    genes = {}  # gene_id -> author
    cards = []
    for f in sorted(ROOT.glob("projects/*/scripts/*.py")):
        txt = f.read_text(encoding="utf-8", errors="ignore")[:1500]
        gid = re.search(r"#\s*Gene-ID:\s*(\S+)", txt)
        base = re.search(r"#\s*Based-On:\s*(\S+)", txt)
        auth = re.search(r"#\s*Author:\s*(\S+)", txt)
        if gid and auth:
            genes[gid.group(1)] = auth.group(1)
            cards.append((gid.group(1), base.group(1) if base else "NONE", auth.group(1)))
    out = []
    for gid, base, auth in cards:
        parent_author = genes.get(base)
        if parent_author and parent_author != auth:
            out.append({"agent": parent_author, "points": 15,
                        "note": f"بُني على سكربته {base} بواسطة {auth}"})
    return out

def main():
    events = load_events()
    seen = {(e.get("agent"), e.get("task")) for e in events if e.get("task")}
    all_ev = events + git_trailer_events(seen) + dna_buildon_events()
    agents_yaml = yaml.safe_load((ROOT / ".connect" / "AGENTS.yaml").read_text(encoding="utf-8"))
    scores, history = {}, {}
    for code, meta in agents_yaml.get("agents", {}).items():
        if meta.get("status") == "active":
            scores[code], history[code] = 0, []
    for e in all_ev:
        a = e["agent"]
        scores.setdefault(a, 0)
        history.setdefault(a, [])
        note = e.get("note", "") or (f"مهمة {e['task']}" if e.get("task") else "")
        scores[a] += int(e["points"])
        history[a].append(f"{'+' if int(e['points']) >= 0 else ''}{e['points']} ({note})")
    today = datetime.date.today().isoformat()
    lines = ["# 🏆 TRUST_LEDGER.md — سجل الثقة",
             f"> يتولد آلياً بـ `trust_ledger.py` — آخر توليد: {today}", "",
             "| الأيجنت | النقاط | الرتبة | آخر 5 أحداث |", "|---|---|---|---|"]
    for a in sorted(scores, key=lambda x: (-scores[x], x)):
        lines.append(f"| {a} | {scores[a]} | {rank_of(scores[a])} | {' · '.join(history[a][-5:]) or '—'} |")
    lines += ["", "**الرتب:** 🐜 Scout (0-29) → 🥈 Builder (30-69) → 🥇 Architect (70-149) → 👑 Queen's Guard (150+)",
              "", "*المصادر: TRUST_EVENTS.yaml (دائم) + Git Trailers (إن وُجدت) + بطاقات DNA (مكافأة البناء +15)*", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ تولد سجل الثقة → {OUT.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
