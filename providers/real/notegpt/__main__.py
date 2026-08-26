# -*- coding: utf-8 -*-
"""
================================================================================
🚀 NoteGPT Direct CLI Runner (__main__.py)
================================================================================
يتيح تشغيل إضافة NoteGPT مباشرة من التيرمينال دون الحاجة لأي ملفات خارجية:
    python -m providers.real.notegpt
    python -m providers.real.notegpt "سؤالك هنا"
    python -m providers.real.notegpt --model deepseek-chat "سؤالك"
================================================================================
"""

import sys
import os
import argparse
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

if __package__ in (None, ""):
    # تشغيل مباشر كسكريبت عبر زرار Run في الـ IDE
    _pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if _pkg_root not in sys.path:
        sys.path.insert(0, _pkg_root)
    from providers.real.notegpt.config import NoteGPTConfig, DEFAULT_MODEL
    from providers.real.notegpt.client import NoteGPTClient
    from providers.real.notegpt.discovery import models as models_mod
else:
    # تشغيل كـ Module عبر python -m
    from .config import NoteGPTConfig, DEFAULT_MODEL
    from .client import NoteGPTClient
    from .discovery import models as models_mod


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NoteGPT Direct CLI Runner — التشغيل المباشر لمزود NoteGPT"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default="عرف نفسك في سطرين بالمصري وقولي بتشتغل إزاي.",
        help="السؤال أو الطلب المراد إرساله",
    )
    parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"النموذج المراد استخدامه (الافتراضي: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--list-models", "-l",
        action="store_true",
        help="عرض قائمة النماذج الـ 36 المعتمدة",
    )
    parser.add_argument(
        "--session", "-s",
        default=None,
        help="معرف جلسة سابقة لاستئناف نفس الساندبوكس",
    )

    args = parser.parse_args()

    # 1. عرض النماذج
    if args.list_models:
        models = models_mod.discover_models()
        print(f"\n🧠 كتالوج نماذج NoteGPT المعتمدة ({len(models)} نموذجاً):")
        print("-" * 65)
        for m in models:
            mid = m.get("model_id")
            status = m.get("status")
            lat = m.get("metrics", {}).get("measured_latency_seconds")
            is_r = "🧠 Reasoning" if m.get("capabilities", {}).get("reasoning") else "⚡ Standard"
            print(f"  • {mid:<30} | {is_r:<12} | {lat}s | {status}")
        print("-" * 65)
        return

    print("=" * 75)
    print("🚀 NoteGPT Direct CLI Runner — تشغيل المزود ذاتياً")
    print("=" * 75)

    # 2. تأمين بيانات الحساب من البيئة أو الافتراضية
    if not os.environ.get("NOTEGPT_EMAIL"):
        os.environ["NOTEGPT_EMAIL"] = "um66jywg@emalupe.com"
        os.environ["NOTEGPT_PASSWORD"] = "Password123#$"

    config = NoteGPTConfig()
    client = NoteGPTClient(config=config, model=args.model, conversation_id=args.session)

    print(f"💬 السؤال: '{args.prompt}'")
    print(f"🤖 النموذج: {args.model}")
    print(f"🏷️ الجلسة: {client.session.conversation_id}")
    print("📡 البث المباشر للرد (Live Streaming):")
    print("-" * 50)

    start_t = time.time()
    try:
        for event in client.stream(args.prompt):
            etype = event.get("type")
            if etype == "text":
                print(event.get("content", ""), end="", flush=True)
            elif etype == "reasoning":
                pass
            elif etype == "sandbox":
                print(f"\n[📦 Daytona Sandbox: {event.get('step')}]")
            elif etype == "credit_usage":
                print(f"\n[💳 استهلاك الكريديت: {event.get('credits')}]")
            elif etype == "error":
                print(f"\n❌ خطأ: {event}")
    except KeyboardInterrupt:
        print("\n⛔ تم الإيقاف بواسطة المستخدم.")
    except Exception as e:
        print(f"\n⚠️ استثناء: {e}")

    print("\n" + "-" * 50)
    print(f"⏱️ زمن التنفيذ: {time.time() - start_t:.2f} ثانية")
    print("=" * 75)


if __name__ == "__main__":
    main()
