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
import uuid
from pathlib import Path

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
    from providers.real.notegpt.runtime import request as req_mod
else:
    # تشغيل كـ Module عبر python -m
    from .config import NoteGPTConfig, DEFAULT_MODEL
    from .client import NoteGPTClient
    from .discovery import models as models_mod
    from .runtime import request as req_mod


def main() -> None:
    parser = argparse.ArgumentParser(
        description="NoteGPT Direct CLI Runner — التشغيل المباشر لمزود NoteGPT"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="السؤال أو الطلب المراد إرساله مباشرة",
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
        "--file", "-f",
        default=None,
        help="مسار ملف نصي مخصص للسؤال (مثال: -f my_prompt.txt)",
    )
    parser.add_argument(
        "--session", "-s",
        default=None,
        help="معرف جلسة سابقة لاستئناف نفس الساندبوكس",
    )
    parser.add_argument(
        "--new", "-n",
        action="store_true",
        help="بدء محادثة وساندبوكس جديد وتوليد معرف جلسة جديد",
    )

    args = parser.parse_args()

    # 1. تحديد نص السؤال تلقائياً:
    # أولوية 1: ملف مخصص عبر -f
    # أولوية 2: نص مباشر ممرر في التيرمينال
    # أولوية 3: الملف الثابت المخصص داخل مجلد المزود (prompt.txt)
    default_prompt_file = os.path.join(os.path.dirname(__file__), "prompt.txt")
    prompt_text = None

    if args.file:
        if os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8", errors="replace") as fh:
                prompt_text = fh.read().strip()
            print(f"📂 تم قراءة السؤال من الملف المحدد: {args.file}")
        else:
            print(f"❌ خطأ: الملف المحدد غير موجود: {args.file}")
            return
    elif args.prompt:
        prompt_text = args.prompt
    elif os.path.exists(default_prompt_file):
        with open(default_prompt_file, "r", encoding="utf-8", errors="replace") as fh:
            prompt_text = fh.read().strip()
        print(f"📂 تم قراءة السؤال تلقائياً من: providers/real/notegpt/prompt.txt")

    if not prompt_text:
        prompt_text = "عرف نفسك في سطرين بالمصري وقولي بتشتغل إزاي."

    # 2. عرض النماذج
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

    # 3. بيانات الحساب — من البيئة فقط (30 §2 · 31 §19.5)
    #
    # P1 — كانت هذه الكتلة تحقن توكن جلسة حيّاً + إيميلاً + كلمة مرور **مكتوبة
    # حرفياً** في ملف متتبَّع بـ git. هذا نفس النمط الذي أحصاه ROUND2 §0 في
    # `projects/ngpt/` (29 سراً) والذي يوجد `config.py` كله لمنعه: الحزمة تقرأ
    # الاعتماد من البيئة فقط، ثم كان هذا الـ entrypoint يعيد إدخاله من الخلف.
    #
    # لا تُعَد قيمة افتراضية بديلة: غياب الاعتماد حالة صالحة (المزوّد يعمل
    # كضيف مجهول — 01.06:519)، والمستخدم يُبلَّغ بوضوح بدل أن يُسنَد سراً إلى
    # حساب شخص آخر دون علمه.
    if not NoteGPTConfig().has_credentials:
        print(
            "ℹ️  لا توجد بيانات اعتماد في البيئة — التشغيل كضيف مجهول.\n"
            "    للتشغيل بحساب: صدّر NOTEGPT_SESSION_TOKEN، أو "
            "NOTEGPT_EMAIL + NOTEGPT_PASSWORD."
        )

    # 3. استرجاع أو إنشاء جلسة المحادثة (Active Session)
    session_id = args.session
    active_sess_file = Path(__file__).resolve().parent / "active_session.txt"
    if args.new:
        session_id = str(uuid.uuid4())
        try:
            active_sess_file.write_text(session_id, encoding="utf-8")
        except Exception:
            pass
    elif not session_id and active_sess_file.exists():
        try:
            session_id = active_sess_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    if not session_id:
        ref_sess = Path("projects/ngpt/active_session.txt")
        if ref_sess.exists():
            try:
                session_id = ref_sess.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    if not session_id:
        session_id = str(uuid.uuid4())
        try:
            active_sess_file.write_text(session_id, encoding="utf-8")
        except Exception:
            pass

    config = NoteGPTConfig()
    client = NoteGPTClient(config=config, model=args.model, conversation_id=session_id)

    fake_ip = req_mod.generate_fake_ip()
    print(f"💬 السؤال: '{prompt_text}'")
    print(f"🤖 النموذج: {args.model}")
    print(f"👤 الحساب النشط: {config.email} (Authenticated Session)")
    print(f"🌸 وضع التشغيل: وضع الأيجنتس السحابي (Cloud Linux Sandbox 🤖 - chat_mode: agent)")
    print(f"🛡️ عنوان الـ IP : {fake_ip} (يتغير تلقائياً مع كل سؤال 🔄)")
    print(f"🏷️ الجلسة: {client.session.conversation_id}")
    print("📡 البث المباشر للرد (Live Streaming):")
    print("-" * 50)

    start_t = time.time()
    phase = "init"
    try:
        for event in client.stream(prompt_text):
            etype = event.get("type")
            if etype == "sandbox":
                print(f"\n⚙️  بيئة الـ Sandbox: {event.get('step')}")
            elif etype == "info":
                content = event.get("content") or event.get("step") or ""
                if content:
                    print(f"\n{content}")
            elif etype == "reasoning":
                if phase != "thinking":
                    print("\n🧠 [دورة التفكير والساندبوكس - Agent Loop]:\n", end="", flush=True)
                    phase = "thinking"
                print(event.get("content", ""), end="", flush=True)
            elif etype == "text":
                if phase == "thinking":
                    print("\n\n🤖 [تسليم الكود والحل النهائي]:\n", end="", flush=True)
                    phase = "final"
                print(event.get("content", ""), end="", flush=True)
            elif etype == "tool_call":
                print(f"\n🛠️  استدعاء أداة: {event.get('tool')}")
            elif etype == "credit_usage":
                print(f"\n💳 استهلاك الكريديت: +{event.get('credits')}")
            elif etype == "error":
                print(f"\n❌ خطأ: {event.get('content') or event}")
    except KeyboardInterrupt:
        print("\n⛔ تم الإيقاف بواسطة المستخدم.")
    except Exception as e:
        print(f"\n⚠️ استثناء: {e}")

    print("\n" + "-" * 50)
    print(f"⏱️ زمن التنفيذ: {time.time() - start_t:.2f} ثانية")
    print("=" * 75)


if __name__ == "__main__":
    main()
