#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dna_tree.py — 🧬 شجرة الجينوم (الركن 2 من SWARM-DNA)
يقرأ بطاقات DNA من رؤوس سكربتات projects/{slug}/scripts/*.py
ويولد projects/{slug}/DNA_TREE.md بمخطط Mermaid ملون حسب سجل الثقة.
الألوان: 🟢 مؤلفه Builder فأعلى أو الجين موسوم verified، 🟡 غير مختبر، 🔴 فشل موثق."""
import argparse, re, sys, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STYLES = {
    "green":  "fill:#0d3321,stroke:#22c55e,color:#dcfce7",
    "yellow": "fill:#332b0d,stroke:#eab308,color:#fef9c3",
    "red":    "fill:#330d0d,stroke:#ef4444,color:#fee2e2",
}
EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

def parse_card(path):
    txt = path.read_text(encoding="utf-8", errors="ignore")[:2000]
    def g(field):
        m = re.search(rf"#\s*{field}:\s*(.+)", txt)
        return m.group(1).strip() if m else None
    gid = g("Gene-ID")
    if not gid:
        return None
    return {"file": path.name, "gene": gid, "based": g("Based-On") or "NONE",
            "gen": g("Generation") or "?", "author": (g("Author") or "?").split()[0],
            "mutation": (g("Mutation") or "").strip('"'),
            "status": (g("Status") or "").lower()}

def author_scores():
    ledger = ROOT / ".connect" / "TRUST_LEDGER.md"
    scores = {}
    if ledger.exists():
        for m in re.finditer(r"^\|\s*(\w+)\s*\|\s*(-?\d+)\s*\|", ledger.read_text(encoding="utf-8"), re.M):
            scores[m.group(1)] = int(m.group(2))
    return scores

def color_of(card, scores):
    if card["status"] == "failed":
        return "red"
    if card["status"] == "verified":
        return "green"
    return "green" if scores.get(card["author"], 0) >= 30 else "yellow"

def node_id(gene):
    return "N" + re.sub(r"[^0-9A-Za-z]", "_", gene)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    proj = ROOT / "projects" / a.project
    scripts = sorted((proj / "scripts").glob("*.py"))
    cards = [c for c in (parse_card(f) for f in scripts) if c]
    if not cards:
        print("❌ لا توجد بطاقات DNA في السكربتات", file=sys.stderr)
        return 1
    scores = author_scores()
    genes = {c["gene"] for c in cards}
    lines = [f"# 🧬 DNA_TREE.md — شجرة جينوم مشروع `{a.project}`",
             f"> تتولد آلياً بـ `dna_tree.py` — آخر توليد: {datetime.date.today().isoformat()}",
             "", "```mermaid", "graph TD"]
    styles = []
    for c in cards:
        col = color_of(c, scores)
        nid = node_id(c["gene"])
        label = f"{c['gene'].split('/')[-1]} {EMOJI[col]}<br/>{c['mutation'][:40]}"
        lines.append(f'  {nid}["{label}"]')
        styles.append(f"  style {nid} {STYLES[col]}")
        if c["based"] != "NONE" and c["based"] in genes:
            lines.append(f"  {node_id(c['based'])} --> {nid}")
    lines += styles + ["```", "", "| الملف | الجيل | المؤلف | الحالة | الطفرة |", "|---|---|---|---|---|"]
    for c in cards:
        col = color_of(c, scores)
        lines.append(f"| `{c['file']}` | {c['gen']} | {c['author']} | {EMOJI[col]} | {c['mutation']} |")
    lines += ["", "*🟢 موثوق (verified أو مؤلفه Builder+) · 🟡 لم يُختبر · 🔴 فشل موثق*", ""]
    out = proj / "DNA_TREE.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ تولدت الشجرة → {out.relative_to(ROOT)} ({len(cards)} جين)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
