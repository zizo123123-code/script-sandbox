#!/usr/bin/env python3
# Based-on: connect-plan-claude-genspark/02.00_SWARM_DNA_PROTOCOL.md
"""
pheromone.py — 🐜 لوحة الفيرومونات (إشارات التنسيق بين الأيجنتات).

الأنواع: CLAIM (حجز مهمة) / WARN (تحذير) / TRAIL (مسار ناجح) / NEED (قرار من زيزو)

الأوامر:
    claim   — حجز مهمة:
        python pheromone.py claim --agent AG --target T-007 --ttl 4 [--note "..."]
    release — تحرير حجز:
        python pheromone.py release --agent AG --target T-007
    mark    — ترك إشارة WARN/TRAIL/NEED:
        python pheromone.py mark --type WARN --agent DS --target flaky_api --ttl 72 --note "..."
    scan    — عرض الإشارات السارية (والمنتهية):
        python pheromone.py scan
    sweep   — كنس الإشارات منتهية الـ TTL:
        python pheromone.py sweep

كل إشارة = ملف YAML بسيط في .connect/pheromones/ باسم {TYPE}_{AGENT}_{target}.yaml
— بدون مكتبات خارجية (YAML يدوي بسيط).
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOARD = ROOT / ".connect" / "pheromones"
TYPES = ("CLAIM", "WARN", "TRAIL", "NEED")


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def slugify(target: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", target.lower()).strip("_")


def sig_path(ptype: str, agent: str, target: str) -> Path:
    return BOARD / f"{ptype}_{agent.upper()}_{slugify(target)}.yaml"


def write_signal(path: Path, data: dict) -> None:
    lines = [f"{k}: {v}" for k, v in data.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_signal(path: Path) -> dict:
    data = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            data[k.strip()] = v.strip().strip('"')
    return data


def is_expired(data: dict) -> bool:
    try:
        expires = dt.datetime.fromisoformat(data["expires"])
        return now() > expires
    except (KeyError, ValueError):
        return True  # إشارة تالفة = هالكة


def all_signals():
    for f in sorted(BOARD.glob("*.yaml")):
        yield f, read_signal(f)


def cmd_claim(args) -> None:
    agent = args.agent.upper()
    # منع سباق المهام: هل فيه CLAIM سارٍ من غيري على نفس الهدف؟
    tslug = slugify(args.target)
    for f, data in all_signals():
        if (
            f.name.startswith("CLAIM_")
            and f.stem.endswith(f"_{tslug}")
            and not is_expired(data)
            and data.get("agent") != agent
        ):
            sys.exit(
                f"⛔ مرفوض: {args.target} محجوزة بالفعل بواسطة {data.get('agent')} "
                f"حتى {data.get('expires')} — خد مهمة تانية."
            )
    path = sig_path("CLAIM", agent, args.target)
    created, expires = now(), now() + dt.timedelta(hours=args.ttl)
    write_signal(path, {
        "type": "CLAIM",
        "agent": agent,
        "target": args.target,
        "created": created.isoformat(timespec="seconds"),
        "expires": expires.isoformat(timespec="seconds"),
        "ttl_hours": args.ttl,
        "note": f'"{args.note}"',
    })
    print(f"✅ CLAIM: {agent} حجز {args.target} حتى {expires.isoformat(timespec='seconds')}")
    print(f"   📄 {path.relative_to(ROOT)}")


def cmd_release(args) -> None:
    path = sig_path("CLAIM", args.agent, args.target)
    if not path.exists():
        sys.exit(f"❌ لا يوجد حجز: {path.name}")
    data = read_signal(path)
    if data.get("agent") != args.agent.upper():
        sys.exit("⛔ مرفوض: لا يمكنك تحرير حجز أيجنت آخر (استخدم sweep لو منتهي)")
    path.unlink()
    print(f"✅ RELEASE: تم تحرير {args.target} من {args.agent.upper()}")


def cmd_mark(args) -> None:
    ptype = args.type.upper()
    if ptype not in ("WARN", "TRAIL", "NEED"):
        sys.exit("❌ mark يقبل WARN / TRAIL / NEED فقط (CLAIM له أمر claim)")
    path = sig_path(ptype, args.agent, args.target)
    created, expires = now(), now() + dt.timedelta(hours=args.ttl)
    write_signal(path, {
        "type": ptype,
        "agent": args.agent.upper(),
        "target": args.target,
        "created": created.isoformat(timespec="seconds"),
        "expires": expires.isoformat(timespec="seconds"),
        "ttl_hours": args.ttl,
        "note": f'"{args.note}"',
    })
    print(f"✅ {ptype}: إشارة من {args.agent.upper()} على {args.target} (TTL {args.ttl}h)")
    print(f"   📄 {path.relative_to(ROOT)}")


def cmd_scan(_args) -> None:
    active, expired = [], []
    for f, data in all_signals():
        (expired if is_expired(data) else active).append((f, data))
    if not active and not expired:
        print("🟢 اللوحة فاضية — لا إشارات.")
        return
    if active:
        print(f"🐜 إشارات سارية ({len(active)}):")
        for f, d in active:
            print(f"  • [{d.get('type')}] {d.get('agent')} → {d.get('target')}"
                  f" | حتى {d.get('expires')} | {d.get('note', '')}")
    if expired:
        print(f"💀 إشارات منتهية ({len(expired)}) — اكنسها بـ sweep:")
        for f, d in expired:
            print(f"  • {f.name}")


def cmd_sweep(_args) -> None:
    removed = 0
    for f, data in list(all_signals()):
        if is_expired(data):
            f.unlink()
            removed += 1
            print(f"🧹 كُنست: {f.name}")
    print(f"✅ sweep: {removed} إشارة اتكنست." if removed else "🟢 لا إشارات منتهية.")


def main() -> None:
    BOARD.mkdir(parents=True, exist_ok=True)
    p = argparse.ArgumentParser(description="🐜 لوحة الفيرومونات")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("claim", help="حجز مهمة")
    c.add_argument("--agent", required=True)
    c.add_argument("--target", required=True)
    c.add_argument("--ttl", type=float, default=4, help="ساعات الصلاحية (افتراضي 4)")
    c.add_argument("--note", default="")
    c.set_defaults(func=cmd_claim)

    r = sub.add_parser("release", help="تحرير حجز")
    r.add_argument("--agent", required=True)
    r.add_argument("--target", required=True)
    r.set_defaults(func=cmd_release)

    m = sub.add_parser("mark", help="إشارة WARN/TRAIL/NEED")
    m.add_argument("--type", required=True, choices=["WARN", "TRAIL", "NEED", "warn", "trail", "need"])
    m.add_argument("--agent", required=True)
    m.add_argument("--target", required=True)
    m.add_argument("--ttl", type=float, default=168, help="ساعات الصلاحية (افتراضي أسبوع)")
    m.add_argument("--note", default="")
    m.set_defaults(func=cmd_mark)

    sub.add_parser("scan", help="عرض الإشارات").set_defaults(func=cmd_scan)
    sub.add_parser("sweep", help="كنس المنتهي").set_defaults(func=cmd_sweep)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
