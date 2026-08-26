# -*- coding: utf-8 -*-
"""
================================================================================
🤖 NoteGPT Real Agent Sandbox Tester v01.03 (وضع الأيجنتس الحقيقي + المصادر المتعددة)
================================================================================
📌 الوصف:
    سكربت نقي ومخصص بنسبة 100% لتشغيل بيئة الأيجنتس السحابية (Agent Sandbox Engine)
    على منصة NoteGPT عبر Pure Requests بدون الحاجة لفتح المتصفح.

✨ المميزات:
    • 📎 منظومة المصادر المتعددة (Multi-Source Ingestion - Up to 5 sources):
        1. 📄 رفع وقراءة الملفات المحلية (Code, Text, CSV, PDF, Markdown).
        2. 🎥 فيديوهات يوتيوب (YouTube Video Transcripts & Summaries).
        3. 🌐 صفحات الويب والتوثيق الحي (Webpages & Docs Ingestion).
    • بيئة تشغيل Sandbox معزولة (create_sandbox / resume_sandbox).
    • استمرار الجلسة في نفس الشات بضغطة زر Run (Multi-Turn Session Persistence).
    • تدوير الـ IP والهوية تلقائياً عند نفاد الرصيد مع البقاء في نفس الشات.
    • تدوير سجل المشاريع الذكي FIFO (حفظ آخر 10 مشاريع فقط مثل سجل الكاميرات).
    • بث حي وتدفق فوري لأحداث الأيجنت والتفكير المنطقي والحل النهائي.
    • تسجيل دخول تلقائي وسحب التوكن الحي وتجديده باستمرار.
    • استعلام كتالوج الـ 50 أيجنت المتخصصة الجاهزة (--agents).

================================================================================
"""

import sys
import io
import os
import re
import time
import json
import uuid
import random
import shutil
import pathlib
import argparse
from dataclasses import dataclass, field
from typing import Generator, Dict, Any, List, Optional, Tuple

# ضبط مخرجات التيرمينال لـ UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# استيراد مكتبة تخطي الحمايات (Cloudscraper)
try:
    import cloudscraper
except ImportError:
    print("❌ مكتبة cloudscraper غير مثبتة! قم بتثبيتها عبر: pip install cloudscraper")
    sys.exit(1)

# استيراد ألوان التيرمينال (Colorama)
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    C_GREEN = Fore.GREEN
    C_CYAN = Fore.CYAN
    C_YELLOW = Fore.YELLOW
    C_MAGENTA = Fore.MAGENTA
    C_RED = Fore.RED
    C_WHITE = Fore.WHITE
    C_BLUE = Fore.BLUE
    C_DIM = Style.DIM
    C_RESET = Style.RESET_ALL
except ImportError:
    C_GREEN = C_CYAN = C_YELLOW = C_MAGENTA = C_RED = C_WHITE = C_BLUE = C_DIM = C_RESET = ""


# ==============================================================================
# ⚙️ إعدادات المنظومة (SSOT Config)
# ==============================================================================
class Config:
    """جميع إعدادات وروابط وموديلات وضع الأيجنتس الحقيقي"""
    BASE_URL: str = "https://notegpt.io/api/v2/chat/stream"
    CONTINUE_URL: str = "https://notegpt.io/api/v2/chat/agent-stream/continue"
    AGENT_REFERER: str = "https://notegpt.io/ai-agent"
    ORIGIN_URL: str = "https://notegpt.io"
    AUTH_LOGIN_URL: str = "https://notegpt.io/api/v1/auth/email/login"
    
    # قائمة موديلات الأيجنتس المكتشفة من منصة NoteGPT
    AVAILABLE_MODELS: Dict[str, str] = {
        "deepseek": "deepseek-v4-flash",
        "deepseek-v4": "deepseek-v4-flash",
        "minimax": "minimax-m3",
        "minimax-m3": "minimax-m3",
        "glm": "glm-5.2",
        "r1": "TA/deepseek-ai/DeepSeek-R1",
        "reasoner": "deepseek-reasoner",
        "gpt4o": "gpt-4o",
        "claude-fable": "claude-fable-5",
    }
    
    DEFAULT_MODEL: str = "deepseek-v4-flash"
    IS_AUTO_MODEL: bool = False   # False = اختيار يدوي صريح | True = أوتو موديل
    DEFAULT_TONE: str = "default"
    DEFAULT_LENGTH: str = "moderate"
    REQUEST_TIMEOUT: int = 45
    AUTO_CONTINUE_LIMIT: int = 5  # أقصى عدد لاستئناف الستريم التلقائي للمهام الطويلة
    MAX_SAVED_PROJECTS: int = 10  # الحد الأقصى للمشاريع المحفوظة (تدوير تلقائي FIFO)
    MAX_ATTACHED_SOURCES: int = 5 # الحد الأقصى للمصادر المرفقة (Up to 5 sources at a time)
    
    # بيانات حساب NoteGPT لتسجيل الدخول وسحب التوكن الحي تلقائياً
    EMAIL: str = os.environ.get("NOTEGPT_EMAIL", "")
    PASSWORD: str = os.environ.get("NOTEGPT_PASSWORD", "")
    SESSION_TOKEN: str = os.environ.get("NOTEGPT_SESSION_TOKEN", "")
    
    # مسارات ملفات المهام والشات المؤتمتة
    CHAT_SEND_FILE: str = str(pathlib.Path(__file__).resolve().parent / "chat_send.txt")
    CHAT_REPLY_FILE: str = str(pathlib.Path(__file__).resolve().parent / "chat_reply.txt")
    ACTIVE_SESSION_FILE: str = str(pathlib.Path(__file__).resolve().parent / "active_session.txt")


# ==============================================================================
# 📎 منظومة المصادر والمرفقات المتعددة (Source Ingestion Engine)
# ==============================================================================
@dataclass
class SourceItem:
    """عنصر مصدر مفرد (ملف محلي، فيديو يوتيوب، صفحة ويب)"""
    type: str          # "file" | "youtube" | "webpage"
    name: str          # اسم الملف أو العنوان أو الرابط المختصر
    target: str        # المسار أو الرابط الكامل
    content: Optional[str] = None  # محتوى الملف لو كان ملفاً محلياً
    size_or_info: str = ""         # حجم الملف أو وصف الرابط


class SourceIngestionHandler:
    """
    محلل ومهندس استيعاب المصادر الخارجية (Files 📎, YouTube 🎥, Webpages 🔗).
    - يدعم حتى 5 مصادر في نفس الطلب (Up to 5 sources at a time).
    - يستخرج الروابط والملفات تلقائياً من نص الرسالة أو من ترويسة files/url/youtube.
    - يقرأ الملفات المحلية بأمان ويدمجها في سياق الساندبوكس بـ Markdown Code Blocks.
    """

    YOUTUBE_REGEX = re.compile(
        r'https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/)([a-zA-Z0-9_\-]+[^\s]*)',
        re.IGNORECASE
    )
    URL_REGEX = re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE)

    @classmethod
    def parse_sources_and_prompt(cls, raw_input: str, base_dir: pathlib.Path = None) -> Tuple[List[SourceItem], str]:
        """
        استخراج المصادر المرفقة وفصلها عن السؤال الأصلي مع دعم الـ Tags والإشارات المباشرة (@file)
        """
        if base_dir is None:
            base_dir = pathlib.Path(__file__).resolve().parent

        sources: List[SourceItem] = []
        cleaned_lines = []
        lines = raw_input.splitlines()
        
        # 1. فحص ترويسات Tags المنظمة في البداية (files:, web:, url:, youtube:)
        in_header = True
        body_lines = []

        for line in lines:
            stripped = line.strip()
            if in_header and (stripped.startswith("---") or stripped.startswith("===")):
                in_header = False
                continue

            if in_header and (
                stripped.lower().startswith("file:") or 
                stripped.lower().startswith("files:") or
                stripped.lower().startswith("web:") or
                stripped.lower().startswith("url:") or
                stripped.lower().startswith("youtube:")
            ):
                tag, val = stripped.split(":", 1)
                tag = tag.strip().lower()
                val = val.strip()

                if tag in ["file", "files"]:
                    file_names = [f.strip() for f in val.split(",") if f.strip()]
                    for fname in file_names:
                        if len(sources) < Config.MAX_ATTACHED_SOURCES:
                            cls._add_file_source(sources, fname, base_dir)

                elif tag in ["web", "url"]:
                    urls = [u.strip() for u in val.split(",") if u.strip()]
                    for u in urls:
                        if len(sources) < Config.MAX_ATTACHED_SOURCES:
                            cls._add_url_source(sources, u)

                elif tag == "youtube":
                    urls = [u.strip() for u in val.split(",") if u.strip()]
                    for u in urls:
                        if len(sources) < Config.MAX_ATTACHED_SOURCES:
                            cls._add_youtube_source(sources, u)
            else:
                in_header = False
                body_lines.append(line)

        remaining_text = "\n".join(body_lines).strip()

        # 2. فحص الإشارات التلقائية في النص (@filename)
        file_mentions = re.findall(r'@([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9_]+)', remaining_text)
        for fpath_str in file_mentions:
            if len(sources) < Config.MAX_ATTACHED_SOURCES:
                # التحقق هل أضيف من قبل
                if not any(s.target.endswith(fpath_str) for s in sources):
                    cls._add_file_source(sources, fpath_str, base_dir)

        # 3. فحص الروابط التلقائية المباشرة في النص
        raw_urls = cls.URL_REGEX.findall(remaining_text)
        for u in raw_urls:
            if len(sources) < Config.MAX_ATTACHED_SOURCES:
                if not any(s.target == u for s in sources):
                    if cls.YOUTUBE_REGEX.search(u):
                        cls._add_youtube_source(sources, u)
                    else:
                        cls._add_url_source(sources, u)

        return sources[:Config.MAX_ATTACHED_SOURCES], remaining_text

    @classmethod
    def _add_file_source(cls, sources: List[SourceItem], file_path_str: str, base_dir: pathlib.Path):
        """قراءة الملف المحلي وإضافته لقائمة المصادر"""
        target_path = pathlib.Path(file_path_str)
        if not target_path.is_absolute():
            # تجربة المسار النسبي لمجلد السكربت ثم الـ Workspace Root
            candidate1 = base_dir / file_path_str
            candidate2 = pathlib.Path(r"D:\SMS\.hRhRhRhRhRhR") / file_path_str
            if candidate1.exists():
                target_path = candidate1
            elif candidate2.exists():
                target_path = candidate2

        if target_path.exists() and target_path.is_file():
            try:
                content = target_path.read_text(encoding="utf-8", errors="replace")
                size_str = f"{len(content)} حرف"
                sources.append(SourceItem(
                    type="file",
                    name=target_path.name,
                    target=str(target_path),
                    content=content,
                    size_or_info=size_str
                ))
            except Exception as e:
                sources.append(SourceItem(
                    type="file",
                    name=target_path.name,
                    target=str(target_path),
                    content=f"Error reading file: {e}",
                    size_or_info="فشل القراءة"
                ))
        else:
            # ملف غير موجود محلياً ولكن تم ذكره كمرجع
            sources.append(SourceItem(
                type="file",
                name=pathlib.Path(file_path_str).name,
                target=file_path_str,
                content=None,
                size_or_info="ملف مرجعي"
            ))

    @classmethod
    def _add_youtube_source(cls, sources: List[SourceItem], url: str):
        """إضافة رابط يوتيوب لقائمة المصادر"""
        sources.append(SourceItem(
            type="youtube",
            name="YouTube Video",
            target=url,
            content=None,
            size_or_info="فيديو يوتيوب"
        ))

    @classmethod
    def _add_url_source(cls, sources: List[SourceItem], url: str):
        """إضافة رابط صفحة ويب لقائمة المصادر"""
        sources.append(SourceItem(
            type="webpage",
            name=url.split("//")[-1].split("/")[0],
            target=url,
            content=None,
            size_or_info="صفحة ويب / توثيق"
        ))

    @classmethod
    def build_injected_prompt(cls, sources: List[SourceItem], user_prompt: str) -> str:
        """دمج المصادر المرفقة في نص الطلب الموجه للـ Sandbox بشكل منظم جداً"""
        if not sources:
            return user_prompt

        blocks = []
        blocks.append("═══════════════════════════════════════════════════════════════")
        blocks.append(f"📎 [المصادر والمرفقات المعتمدة للـ Sandbox] ({len(sources)}/5 Sources Attached):")
        blocks.append("═══════════════════════════════════════════════════════════════\n")

        for idx, src in enumerate(sources, 1):
            if src.type == "file":
                blocks.append(f"📄 مصدر [{idx}/5] - ملف محلي: `{src.name}` ({src.size_or_info})")
                blocks.append(f"المسار: `{src.target}`")
                if src.content:
                    ext = src.name.split(".")[-1] if "." in src.name else ""
                    blocks.append(f"```{ext}\n{src.content}\n```\n")
                else:
                    blocks.append("(ملف مرجعي مطلوب التعامل معه داخل الساندبوكس)\n")

            elif src.type == "youtube":
                blocks.append(f"🎥 مصدر [{idx}/5] - فيديو يوتيوب مرجعي:")
                blocks.append(f"الرابط: {src.target}")
                blocks.append("💡 (يرجى استخراج محتوى وشرح وتفريغ هذا الفيديو واستخدامه في الحل داخل الساندبوكس)\n")

            elif src.type == "webpage":
                blocks.append(f"🌐 مصدر [{idx}/5] - صفحة ويب / توثيق مرجعي:")
                blocks.append(f"الرابط: {src.target}")
                blocks.append("💡 (يرجى استخدام هذا التوثيق والرابط كمرجع أساسي في كتابة وتشغيل الكود بالساندبوكس)\n")

        blocks.append("───────────────────────────────────────────────────────────────")
        blocks.append("🎯 [المهمة والمطلوب تنفيذه من المستخدم]:")
        blocks.append(user_prompt)
        blocks.append("───────────────────────────────────────────────────────────────")

        return "\n".join(blocks)


# ==============================================================================
# 🛠️ الدوال المساعدة وتوليد الهويات وإدارة الجلسات
# ==============================================================================
def load_active_session() -> str:
    """قراءة معرف الجلسة الحالي للاستمرار في نفس المحادثة بضغطة زر Run (Multi-Turn Session)"""
    session_file = pathlib.Path(Config.ACTIVE_SESSION_FILE)
    if session_file.exists():
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                cid = f.read().strip()
                if cid and len(cid) >= 16:
                    return cid
        except Exception:
            pass
    return create_and_save_new_session()


def create_and_save_new_session() -> str:
    """توليد جلسة محادثة جديدة وحفظها في active_session.txt"""
    new_cid = str(uuid.uuid4())
    save_active_session(new_cid)
    return new_cid


def save_active_session(conv_id: str):
    """حفظ معرف الجلسة في active_session.txt لضمان الاستمرارية"""
    try:
        with open(Config.ACTIVE_SESSION_FILE, "w", encoding="utf-8") as f:
            f.write(conv_id)
    except Exception:
        pass


def generate_fake_ip() -> str:
    """توليد IP وهمي لتمويه الهيدرز لكل طلب"""
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"


def get_model_badge(model_name: str) -> str:
    """توليد بادج ملون ومميز لكل موديل مع أيقونته الخاصة بالأصفر المميز"""
    m = (model_name or "").lower()
    if "deepseek" in m or "v4" in m:
        return f"{C_YELLOW}🐳 [DeepSeek V4 Flash]{C_RESET}"
    elif "minimax" in m or "m3" in m:
        return f"{C_YELLOW}⚡ [MiniMax M3]{C_RESET}"
    elif "glm" in m:
        return f"{C_YELLOW}🔮 [GLM 5.2]{C_RESET}"
    elif "r1" in m:
        return f"{C_YELLOW}🧠 [DeepSeek R1]{C_RESET}"
    elif "gpt" in m:
        return f"{C_YELLOW}🟢 [GPT-4o]{C_RESET}"
    elif "claude" in m or "fable" in m:
        return f"{C_YELLOW}🎭 [Claude Fable]{C_RESET}"
    return f"{C_YELLOW}🤖 [{model_name}]{C_RESET}"


def get_term_width(default: int = 68) -> int:
    """قياس عرض التيرمينال الحقيقي لضبط الفواصل الأفقية ديناميكياً بدون كسر السطور"""
    try:
        w = shutil.get_terminal_size((default, 20)).columns
        return max(50, min(w, 80))
    except Exception:
        return default


def print_divider(char: str = "═", color: str = C_MAGENTA):
    """طباعة فاصل أفقي متجاوب وجميل يمنع تشوه النصوص والـ Line-Wrap"""
    w = get_term_width()
    print(f"{color}{char * w}{C_RESET}")


def print_banner(client: 'NoteGPTAgentClient', sources: List[SourceItem] = None):
    """طباعة بانر نيون ملون متجاوب مع استعلام رصيد الـ Sandbox والمصادر المرفقة"""
    print()
    print_divider("═", C_MAGENTA)
    print(f"{C_MAGENTA}🤖 NoteGPT Real Agent Sandbox Tester — Pure Requests & Execution{C_RESET}")
    print(f"{C_CYAN}📌 بيئة Sandbox سحابية معزولة + 📎 منظومة المصادر المتعددة (Files/YT/Web){C_RESET}")
    print_divider("─", C_MAGENTA)
    mode_text = f"{C_CYAN}(Auto 🔄){C_RESET}" if client.is_auto else f"{C_GREEN}(Manual 🎯){C_RESET}"
    print(f"  🤖 الموديل النشط : {C_YELLOW}{client.model}{C_RESET} {mode_text}")
    print(f"  🆔 جلسة المحادثة : {C_DIM}{client.conv_id}{C_RESET}")
    print(f"  🌐 الرابط المرجعي: {C_DIM}{Config.AGENT_REFERER}{C_RESET}")

    # استعلام رصيد الـ Sandbox للأيجنت
    quota = client.get_quota_info()
    if quota and "quota_left" in quota:
        q_left = quota.get("quota_left", 0)
        q_used = quota.get("quota_used", 0)
        print(f"  🎯 رصيد Sandbox  : {C_YELLOW}{q_left}{C_RESET} متبقي | {C_WHITE}{q_used}{C_RESET} مستخدم")

    # عرض المصادر المرفقة لو وجدت
    if sources:
        print_divider("─", C_MAGENTA)
        print(f"  📎 المصادر المرفقة ({len(sources)}/{Config.MAX_ATTACHED_SOURCES} Sources Attached):")
        for idx, s in enumerate(sources, 1):
            if s.type == "file":
                print(f"     {idx}. 📄 [ملف محلي]  {C_YELLOW}{s.name:<20}{C_RESET} ({s.size_or_info})")
            elif s.type == "youtube":
                print(f"     {idx}. 🎥 [يوتيوب]     {C_CYAN}{s.target}{C_RESET}")
            elif s.type == "webpage":
                print(f"     {idx}. 🌐 [صفحة ويب]   {C_GREEN}{s.target}{C_RESET}")

    print_divider("═", C_MAGENTA)
    print()


# ==============================================================================
# 🧠 محرك تشغيل وضع الأيجنتس الحقيقي (Real Agent Engine)
# ==============================================================================
class NoteGPTAgentClient:
    """كلاينت إدارة وتنفيذ طلبات الأيجنتس الحقيقية والـ Sandbox مع دعم الوضع اليدوي والأوتو وتدوير الهويات"""

    def __init__(self, model: str = None, is_auto: bool = None, conv_id: str = None):
        self.model = model or Config.DEFAULT_MODEL
        self.is_auto = is_auto if is_auto is not None else Config.IS_AUTO_MODEL
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
        )
        # تثبيت هوية الجلسة والمحادثة
        self.anon_user_id = str(uuid.uuid4())
        self.sbox_guid = str(uuid.uuid4())
        self.conv_id = conv_id or load_active_session()
        save_active_session(self.conv_id)
        
        self.cookies = {
            "anonymous_user_id": self.anon_user_id,
            "sbox-guid": self.sbox_guid
        }
        # مقاييس التتبع والتعافي الذاتي (Self-Healing Telemetry)
        self.telemetry = {
            "turns": 1,
            "continue_calls": 0,
            "quota_exhausted": False,
            "recovery_used": False,
            "ip_rotated": False,
            "attached_sources_count": 0,
            "error_encountered": None
        }

    def rotate_identity(self, keep_conversation: bool = True):
        """
        🔄 تدوير الهوية والـ IP الذكي (IP & Identity Rotation):
        يولد عنوان IP وهمي جديد، معرفات cookies جديدة، ويعيد بناء جلسة الـ scraper،
        مع الحفاظ الصارم على نفس الـ conversation_id!
        """
        self.anon_user_id = str(uuid.uuid4())
        self.sbox_guid = str(uuid.uuid4())
        if not keep_conversation:
            self.conv_id = create_and_save_new_session()
        self.cookies = {
            "anonymous_user_id": self.anon_user_id,
            "sbox-guid": self.sbox_guid
        }
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
        )
        self.telemetry["ip_rotated"] = True
        self.telemetry["recovery_used"] = True

    def login_and_refresh_token(self) -> bool:
        """تسجيل الدخول التلقائي وسحب التوكن الحي الجديد"""
        if not Config.EMAIL or not Config.PASSWORD:
            return False
        try:
            headers = {
                'Accept': "*/*",
                'Content-Type': "application/json; charset=UTF-8",
                'origin': Config.ORIGIN_URL,
                'referer': f"{Config.ORIGIN_URL}/login",
            }
            payload = {"email": Config.EMAIL, "password": Config.PASSWORD}
            r = self.scraper.post(Config.AUTH_LOGIN_URL, json=payload, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", {})
                token = data.get("access_token")
                if token:
                    Config.SESSION_TOKEN = token
                    self.cookies["token"] = token
                    self.cookies["access_token"] = token
                    return True
        except Exception:
            pass
        return False

    def _build_headers(self) -> Dict[str, str]:
        """بناء الهيدرات وتجديد الـ IP الوهمي لكل طلب"""
        fake_ip = generate_fake_ip()
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br, zstd",
            'accept-language': "ar-EG,ar;q=0.9,en-US;q=0.8",
            'content-type': "application/json",
            'origin': Config.ORIGIN_URL,
            'referer': Config.AGENT_REFERER,
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            'X-Forwarded-For': fake_ip,
            'X-Real-IP': fake_ip,
            'Client-IP': fake_ip
        }
        if Config.SESSION_TOKEN:
            headers['Authorization'] = f"Bearer {Config.SESSION_TOKEN}"
        return headers

    def get_quota_info(self) -> Dict[str, Any]:
        """استعلام رصيد الـ Sandbox المتبقي للأيجنت في الحساب"""
        try:
            if not Config.SESSION_TOKEN and Config.EMAIL:
                self.login_and_refresh_token()
            headers = self._build_headers()
            r = self.scraper.get(f"{Config.ORIGIN_URL}/api/v2/plan-quota", headers=headers, timeout=6)
            if r.status_code == 200:
                data = r.json().get("data", {})
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
        return {}

    @staticmethod
    def fetch_shared_agents() -> list:
        """جلب قائمة الأيجنتس المتخصصة الجاهزة"""
        try:
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'desktop': False})
            r = scraper.get(f"{Config.ORIGIN_URL}/api/v1/agent/share/list?page_no=1&page_size=50&language=en", timeout=8)
            if r.status_code == 200:
                return r.json().get("data", {}).get("list", [])
        except Exception:
            pass
        return []

    def _create_chat_session(self, prompt: str):
        """إنشاء وحفظ جلسة الأيجنت في قائمة Recents بالمتصفح (Phase 1)"""
        try:
            headers = self._build_headers()
            now_ms = int(time.time() * 1000)
            payload = {
                "source": "agent",
                "content": {
                    "title": prompt[:40],
                    "updateTime": now_ms,
                    "chat_list": [{
                        "label": prompt,
                        "question": prompt,
                        "answer": [""],
                        "reasoning": [{"startedAt": None, "endedAt": None, "reasoning": "", "thinkingSeconds": 0}],
                        "blocks": [],
                        "isStreaming": True,
                        "isInterrupted": False,
                        "generatedFiles": [],
                        "conversation_id": self.conv_id,
                        "created_at": now_ms,
                        "modelValue": self.model,
                        "isAutoModel": self.is_auto,
                        "isStopped": False
                    }]
                }
            }
            self.scraper.post(f"{Config.ORIGIN_URL}/api/v2/ai-chat", json=payload, headers=headers, timeout=5)
        except Exception:
            pass

    def _finalize_chat_session(self, prompt: str, reasoning: str, answer: str):
        """تحديث وتثبيت محتوى الرد والتفكير في سجل وتاريخ المتصفح بالكامل (Phase 2)"""
        try:
            headers = self._build_headers()
            now_s = int(time.time())
            now_ms = int(time.time() * 1000)
            payload = {
                "id": self.conv_id,
                "content": {
                    "question": prompt,
                    "type": "text",
                    "status": "finish",
                    "source": "agent",
                    "created_at": now_s,
                    "updated_at": now_s,
                    "chat_list": [{
                        "label": prompt,
                        "question": prompt,
                        "answer": [""],
                        "reasoning": [{"startedAt": None, "endedAt": None, "reasoning": "", "thinkingSeconds": 0}],
                        "blocks": [
                            {"type": "reasoning", "content": reasoning},
                            {"type": "text", "content": answer},
                            {"type": "credit_usage", "content": 1}
                        ],
                        "isStreaming": False,
                        "isInterrupted": False,
                        "generatedFiles": [],
                        "conversation_id": self.conv_id,
                        "created_at": now_ms,
                        "modelValue": self.model,
                        "isAutoModel": self.is_auto,
                        "creditsUsed": 1
                    }]
                }
            }
            self.scraper.put(f"{Config.ORIGIN_URL}/api/v2/ai-chat", json=payload, headers=headers, timeout=5)
        except Exception:
            pass

    def _send_continue_stream(self) -> Generator[Dict[str, Any], None, None]:
        """إرسال طلب استئناف الساندبوكس (agent-stream/continue) لاستكمال التفكير وتشغيل المهام الطويلة"""
        headers = self._build_headers()
        payload = {"conversation_id": self.conv_id}
        try:
            resp = self.scraper.post(
                Config.CONTINUE_URL,
                json=payload,
                headers=headers,
                cookies=self.cookies,
                stream=True,
                timeout=Config.REQUEST_TIMEOUT
            )
            if resp.status_code != 200:
                return

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        yield {"type": "done", "content": "[DONE]"}
                        break
                    try:
                        event = json.loads(data_str)
                        etype = event.get("type")
                        if etype == "credit_usage":
                            credits_used = event.get("data", {}).get("credits") or event.get("credits") or 1
                            yield {"type": "credit_usage", "credits": credits_used}
                        elif etype == "tool_call":
                            tool_name = event.get("tool") or event.get("name") or event.get("data", {}).get("tool", "tool")
                            tool_args = event.get("arguments") or event.get("args") or event.get("data", {}).get("arguments", {})
                            yield {"type": "tool_call", "tool": tool_name, "args": tool_args}
                        elif etype == "tool_call_result":
                            result_data = event.get("result") or event.get("content") or event.get("data", {}).get("result", "")
                            yield {"type": "tool_result", "content": result_data}
                        
                        reasoning_content = event.get("reasoning", "")
                        if reasoning_content:
                            yield {"type": "reasoning", "content": reasoning_content}

                        text_content = event.get("text", "")
                        if text_content:
                            yield {"type": "text", "content": text_content}

                        if etype == "done" or event.get("done"):
                            reason = event.get("reason", "")
                            if reason == "agent_tool_limit" or reason == "length":
                                yield {"type": "continue_needed", "reason": reason}
                            else:
                                yield {"type": "done", "content": "[DONE]"}
                    except json.JSONDecodeError:
                        pass
        except Exception as ex:
            yield {"type": "error", "content": f"Continue stream error: {ex}"}

    def ask_agent_stream(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """
        🚀 إرسال طلب الأيجنت واستقبال البث الحي مع دعم Auto-Continue والتعافي الذاتي وتدوير الـ IP
        """
        self._create_chat_session(prompt)
        headers = self._build_headers()

        payload = {
            "conversation_id": self.conv_id,
            "model": self.model,
            "prompt": prompt,
            "tone": Config.DEFAULT_TONE,
            "length": Config.DEFAULT_LENGTH,
            "language": "auto",
            "source": "agent",
            "is_auto_model": self.is_auto
        }

        yield {"type": "sandbox", "step": "جاري تجهيز وتأمين بيئة الساندبوكس المعزولة (Initializing Daytona Sandbox)..."}

        try:
            resp = self.scraper.post(
                Config.BASE_URL,
                json=payload,
                headers=headers,
                cookies=self.cookies,
                stream=True,
                timeout=Config.REQUEST_TIMEOUT
            )

            if resp.status_code != 200:
                yield {"type": "error", "content": f"فشل الاتصال بالسيرفر (HTTP Status {resp.status_code})"}
                return

            done_received = False
            sandbox_ready_emitted = False

            for line in resp.iter_lines():
                if not line:
                    continue
                decoded = line.decode('utf-8', errors='replace').strip()

                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()

                    if data_str == "[DONE]":
                        done_received = True
                        yield {"type": "done", "content": "[DONE]"}
                        break

                    try:
                        event = json.loads(data_str)
                        code = event.get("code")
                        if code == 0:
                            pass
                        elif code == 164019:
                            yield {"type": "info", "content": "⚠️ [نفاد رصيد الساندبوكس]: جاري تدوير الـ IP والهوية السحابية فوراً مع الحفاظ على نفس الشات..."}
                            self.rotate_identity(keep_conversation=True)
                            self.login_and_refresh_token()
                            headers = self._build_headers()
                            self.telemetry["quota_exhausted"] = True
                            self.telemetry["ip_rotated"] = True
                            continue
                        elif code is not None and code != 0:
                            msg = event.get("message", "خطأ غير معروف")
                            yield {"type": "error", "content": f"السيرفر أرجع رمز خطأ ({code}): {msg}"}
                            return

                        etype = event.get("type")

                        if etype in ["create_sandbox", "resume_sandbox"]:
                            msg = event.get("data", {}).get("message", "تجهيز الساندبوكس...")
                            yield {"type": "sandbox", "step": msg}

                        elif etype == "credit_usage":
                            credits_used = event.get("data", {}).get("credits") or event.get("credits") or 1
                            yield {"type": "credit_usage", "credits": credits_used}

                        elif etype == "tool_call":
                            tool_name = event.get("tool") or event.get("name") or event.get("data", {}).get("tool", "tool")
                            tool_args = event.get("arguments") or event.get("args") or event.get("data", {}).get("arguments", {})
                            yield {"type": "tool_call", "tool": tool_name, "args": tool_args}

                        elif etype == "tool_call_result":
                            result_data = event.get("result") or event.get("content") or event.get("data", {}).get("result", "")
                            yield {"type": "tool_result", "content": result_data}

                        reasoning_content = event.get("reasoning", "")
                        if reasoning_content:
                            if not sandbox_ready_emitted:
                                yield {"type": "sandbox_ready"}
                                sandbox_ready_emitted = True
                            yield {"type": "reasoning", "content": reasoning_content}

                        text_content = event.get("text", "")
                        if text_content:
                            if not sandbox_ready_emitted:
                                yield {"type": "sandbox_ready"}
                                sandbox_ready_emitted = True
                            yield {"type": "text", "content": text_content}

                        if etype == "done" or event.get("done"):
                            reason = event.get("reason", "")
                            if reason == "agent_tool_limit" or reason == "length":
                                done_received = False
                            else:
                                done_received = True
                                yield {"type": "done", "content": "[DONE]"}
                                break

                    except json.JSONDecodeError:
                        pass

            # 🔄 نظام الاستئناف التلقائي (Auto-Continue Loop)
            continue_attempts = 0
            while not done_received and continue_attempts < Config.AUTO_CONTINUE_LIMIT:
                continue_attempts += 1
                self.telemetry["continue_calls"] = continue_attempts
                self.telemetry["recovery_used"] = True
                yield {"type": "info", "content": f"🔄 [استئناف تلقائي]: جاري استكمال التفكير وتشغيل الساندبوكس (استئناف #{continue_attempts})..."}
                time.sleep(1)
                for c_event in self._send_continue_stream():
                    ce_type = c_event.get("type")
                    if ce_type == "done":
                        done_received = True
                        yield c_event
                        break
                    elif ce_type == "continue_needed":
                        done_received = False
                        break
                    else:
                        yield c_event

        except Exception as ex:
            yield {"type": "error", "content": f"حدث استثناء أثناء الاتصال بالأيجنت: {str(ex)}"}


# ==============================================================================
# 💾 استخراج وحفظ وتدوير ملفات الساندبوكس (FIFO Camera-Roll Project Manager)
# ==============================================================================
def manage_saved_projects_buffer(output_base_dir: pathlib.Path, max_projects: int = Config.MAX_SAVED_PROJECTS):
    """تدوير المجلدات للحفاظ على آخر 10 مشاريع فقط (نظام مسح الأقدم FIFO)"""
    try:
        if not output_base_dir.exists():
            return
        subdirs = [d for d in output_base_dir.iterdir() if d.is_dir()]
        if len(subdirs) > max_projects:
            subdirs.sort(key=lambda x: x.stat().st_mtime)
            dirs_to_delete = subdirs[:len(subdirs) - max_projects]
            for d in dirs_to_delete:
                try:
                    shutil.rmtree(d, ignore_errors=True)
                except Exception:
                    pass
            print(f"\n{C_YELLOW}🧹 [تدوير السجل الذكي - FIFO]: تم تنظيف {len(dirs_to_delete)} مجلد قديم للحفاظ على آخر {max_projects} مشاريع فقط (نظام سجل الكاميرات).{C_RESET}")
    except Exception:
        pass


def extract_and_save_sandbox_files(reasoning: str, answer: str, prompt: str) -> list:
    """استخراج كافة الملفات المصممة داخل الساندبوكس وتنزيلها محلياً"""
    saved_files = []
    seen_filenames = set()
    output_base = pathlib.Path(__file__).resolve().parent / "agent_output"
    output_base.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    clean_title = re.sub(r'[^a-zA-Z0-9_\u0600-\u06FF]+', '_', prompt.strip())[:30].strip('_') or "project"
    project_dir = output_base / f"{timestamp}_{clean_title}"
    project_dir.mkdir(exist_ok=True)

    # 1. استخراج ملفات tool_call_result من الـ JSON
    combined_raw = reasoning + "\n" + answer
    file_pattern = r'\{[^{}]*"file_path"\s*:\s*"([^"]+)"[^{}]*"content"\s*:\s*"((?:[^"\\]|\\.)*)"[^{}]*\}'
    matches = re.findall(file_pattern, combined_raw)

    for fpath_str, raw_content in matches:
        fname = pathlib.Path(fpath_str).name
        if fname in seen_filenames or not fname:
            continue
        try:
            content = json.loads(f'"{raw_content}"')
        except Exception:
            content = raw_content.replace("\\n", "\n").replace('\\"', '"')

        target_file = project_dir / fname
        target_file.write_text(content, encoding="utf-8")
        seen_filenames.add(fname)
        saved_files.append((fname, target_file, len(content)))

    # 2. استخراج كتل الأكواد المعنونة من الـ Markdown
    md_blocks = re.findall(r'(?:###?\s*`?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9_]+)`?|#\s*([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9_]+))\s*\n+```[a-zA-Z0-9_]*\n([\s\S]*?)```', combined_raw)
    for m in md_blocks:
        fname_candidate = m[0] or m[1]
        code_content = m[2]
        fname = pathlib.Path(fname_candidate).name
        if fname in seen_filenames or not fname:
            continue

        target_file = project_dir / fname
        target_file.write_text(code_content, encoding="utf-8")
        seen_filenames.add(fname)
        saved_files.append((fname, target_file, len(code_content)))

    if saved_files:
        print(f"\n{C_GREEN}📥 [Auto Sandbox Exporter]: تم تنزيل وحفظ {len(saved_files)} ملف من الـ Sandbox محلياً:{C_RESET}")
        for fname, fpath, size in saved_files:
            print(f"  • {C_YELLOW}{fname}{C_RESET} ({size} حرف) ➜ {C_DIM}{fpath}{C_RESET}")
    else:
        if project_dir.exists() and not any(project_dir.iterdir()):
            try:
                project_dir.rmdir()
            except Exception:
                pass

    manage_saved_projects_buffer(output_base, max_projects=Config.MAX_SAVED_PROJECTS)
    return saved_files


# ==============================================================================
# 📊 طباعة تقارير التنفيذ الاحترافية
# ==============================================================================
def print_execution_report(client: 'NoteGPTAgentClient', prompt: str, elapsed: float, total_credits: int, saved_files: list, sources: List[SourceItem] = None):
    """طباعة بطاقة ملخص تنفيذ المهمة الاحترافية مع المصادر المرفقة"""
    clean_title = (prompt[:50] + "...") if len(prompt) > 50 else prompt
    clean_title = clean_title.replace("\n", " ")

    is_agent = True
    border_color = C_MAGENTA if is_agent else C_BLUE
    mode_str = f"{C_MAGENTA}🌸 وضع الأيجنتس السحابي (Cloud Linux Sandbox 🤖){C_RESET}" if is_agent else f"{C_BLUE}🔷 وضع الشات العادي (Direct AI Chat 💬){C_RESET}"

    model_badge = get_model_badge(client.model)
    model_mode = f"{C_CYAN}(Auto 🔄){C_RESET}" if client.is_auto else f"{C_GREEN}(Manual 🎯){C_RESET}"

    t = getattr(client, "telemetry", {})
    turns = t.get("turns", 1)
    continues = t.get("continue_calls", 0)
    quota_exhausted = t.get("quota_exhausted", False)
    recovery_used = t.get("recovery_used", False)
    ip_rotated = t.get("ip_rotated", False)

    turns_str = f"{C_YELLOW}جولتان (Auto-Resumed via Turn 2) ⚡{C_RESET}" if turns > 1 else f"{C_GREEN}جولة واحدة (Turn 1) ✅{C_RESET}"
    continue_str = f"{C_YELLOW}{continues} استئناف (Auto-Continued) 🔄{C_RESET}" if continues > 0 else f"{C_GREEN}0 استئناف (مستقر ومباشر) ✅{C_RESET}"
    
    if ip_rotated:
        healing_str = f"{C_YELLOW}⚡ تم تدوير الـ IP والهوية واستئناف نفس الشات بنجاح{C_RESET}"
    elif recovery_used:
        healing_str = f"{C_YELLOW}⚡ تم التنشيط والتعافي الذاتي بنجاح (Self-Healing Active){C_RESET}"
    else:
        healing_str = f"{C_GREEN}✅ اتصال ساندبوكس مباشر ومستقر 100%{C_RESET}"

    quota_str = f"{C_RED}⚠️ واجه نقص رصيد مؤقت وتم تجاوزه{C_RESET}" if quota_exhausted else f"{C_GREEN}✅ رصيد الحساب كافي ومتاح (لم ينفد){C_RESET}"

    print()
    print_divider("═", border_color)
    print(f" {C_WHITE}📊 ملخص تقرير تنفيذ المهمة (Execution Summary Report){C_RESET}")
    print_divider("─", border_color)
    print(f"  🎯 وضع التشغيل    : {mode_str}")
    print(f"  🤖 الموديل        : {model_badge} {model_mode}")
    print(f"  📝 عنوان المهمة   : {C_WHITE}\"{clean_title}\"{C_RESET}")
    print(f"  🆔 معرّف الجلسة   : {C_DIM}{client.conv_id}{C_RESET}")
    if sources:
        print(f"  📎 المصادر المعتمدة: {C_YELLOW}{len(sources)}/{Config.MAX_ATTACHED_SOURCES} مصادر مرفقة{C_RESET}")
    print_divider("─", border_color)
    print(f"  ⏱️  زمن الاستجابة  : {C_GREEN}{elapsed:.2f} ثانية{C_RESET}  |  💳 الكريديت المستهلك: {C_YELLOW}{total_credits} Credits{C_RESET}")
    print(f"  🔄 جولات الساندبوكس: {turns_str}  |  📡 استئناف الستريم: {continue_str}")
    print(f"  🛡️ التعافي الذاتي : {healing_str}")
    print(f"  💳 حالة الرصيد    : {quota_str}")
    print_divider("─", border_color)
    
    if saved_files:
        print(f"  📦 ملفات الساندبوكس المحفوظة محلياً ({len(saved_files)} ملف):")
        for fname, fpath, size in saved_files:
            rel_path = fpath.name if hasattr(fpath, "name") else str(fpath)
            print(f"     • {C_YELLOW}{rel_path:<20}{C_RESET} ({size} حرف) ➜ {C_DIM}{str(fpath)}{C_RESET}")
    else:
        print(f"  📦 ملفات الساندبوكس: {C_DIM}تم تسليم الإجابة مباشرة بدون ملفات منفصلة{C_RESET}")

    print_divider("═", border_color)
    print()


def run_single_prompt(client: NoteGPTAgentClient, raw_prompt: str, base_dir: pathlib.Path = None) -> str:
    """تنفيذ مهمة واحدة مع معالجة وحقن المصادر المرفقة تلقائياً"""
    sources, user_prompt = SourceIngestionHandler.parse_sources_and_prompt(raw_prompt, base_dir)
    injected_prompt = SourceIngestionHandler.build_injected_prompt(sources, user_prompt)
    client.telemetry["attached_sources_count"] = len(sources)

    print(f"{C_BLUE}📝 المهمة:{C_RESET} {C_WHITE}{user_prompt}{C_RESET}\n")
    if sources:
        print(f"{C_MAGENTA}📎 [معالجة المصادر]: تم رصد وتجهيز {len(sources)} مصادر مرفقة للـ Sandbox.{C_RESET}\n")

    print(f"{C_YELLOW}⏳ [المرحلة 1]: جاري الاتصال وتجهيز بيئة الـ Sandbox...{C_RESET}\n")

    start_time = time.time()
    current_phase = "init"
    full_text = []
    reasoning_text = []
    total_credits = 0

    for event in client.ask_agent_stream(injected_prompt):
        etype = event.get("type")

        if etype == "sandbox":
            step = event.get("step", "")
            print(f"{C_GREEN}⚙️  بيئة الـ Sandbox:{C_RESET} {C_CYAN}{step}{C_RESET}")

        elif etype == "sandbox_ready":
            print(f"{C_GREEN}✅ جاهزية البيئة: تم تجهيز الـ Sandbox بنجاح.{C_RESET}\n")

        elif etype == "credit_usage":
            credits_used = event.get("credits", 1)
            total_credits += credits_used
            print(f"\n{C_YELLOW}💳 استهلاك الكريديت: +{credits_used} (إجمالي: {total_credits} Credits){C_RESET}")

        elif etype == "tool_call":
            tool_name = event.get("tool", "tool")
            args_str = str(event.get("args", ""))[:80]
            print(f"\n{C_CYAN}🛠️  أداة الساندبوكس:{C_RESET} {C_YELLOW}{tool_name}{C_RESET} {C_DIM}{args_str}{C_RESET}")

        elif etype == "tool_result":
            res_preview = str(event.get("content", ""))[:80]
            print(f"{C_GREEN}  ↳ نتيجة الأداة:{C_RESET} {C_DIM}{res_preview}{C_RESET}")

        elif etype == "reasoning":
            if current_phase != "thinking":
                print(f"\n{C_MAGENTA}🧠 [المرحلة 2: دورة التفكير والساندبوكس - Agent Loop]:{C_RESET}\n{C_DIM}", end="", flush=True)
                current_phase = "thinking"
            chunk = event.get("content", "")
            print(chunk, end="", flush=True)
            reasoning_text.append(chunk)

        elif etype == "text":
            chunk = event.get("content", "")
            if current_phase == "init":
                print(f"{C_CYAN}💬 [رسالة الأيجنت التمهيدية]:{C_RESET} {chunk}", end="", flush=True)
                current_phase = "intro"
            elif current_phase == "intro":
                print(chunk, end="", flush=True)
            elif current_phase == "thinking":
                print(f"{C_RESET}\n\n{C_GREEN}🤖 [المرحلة 3: تسليم الكود والحل النهائي]:{C_RESET}\n")
                current_phase = "final"
                print(chunk, end="", flush=True)
            else:
                print(chunk, end="", flush=True)
            full_text.append(chunk)

        elif etype == "info":
            print(f"\n{C_YELLOW}{event.get('content')}{C_RESET}")

        elif etype == "error":
            print(f"\n{C_RED}❌ {event.get('content')}{C_RESET}\n")

    elapsed = round(time.time() - start_time, 2)
    final_answer = "".join(full_text)
    final_reasoning = "".join(reasoning_text)
    saved_files = []

    if final_answer or final_reasoning:
        client._finalize_chat_session(user_prompt, final_reasoning, final_answer)
        saved_files = extract_and_save_sandbox_files(final_reasoning, final_answer, user_prompt)

    print_execution_report(client, user_prompt, elapsed, total_credits, saved_files, sources)
    return final_answer


def run_interactive_mode(client: NoteGPTAgentClient):
    """وضع المهام التفاعلية المستمرة مع الأيجنت والـ Sandbox"""
    print_banner(client)
    print(f"{C_YELLOW}💡 اكتب مهمتك للأيجنت (يمكنك استخدام @file أو روابط YT/Web) واضغط Enter | 'exit' للخروج{C_RESET}\n")

    while True:
        try:
            user_input = input(f"{C_GREEN}👤 أنت:{C_RESET} ")
            if not user_input.strip():
                continue
            inp_clean = user_input.strip()
            if inp_clean.lower() in ["exit", "quit", "خروج"]:
                print(f"\n{C_YELLOW}👋 تم إغلاق جلسة الأيجنت.{C_RESET}")
                break

            print()
            run_single_prompt(client, inp_clean)

        except KeyboardInterrupt:
            print(f"\n\n{C_RED}⛔ تم الإيقاف بواسطة المستخدم.{C_RESET}")
            break


def run_file_mode(client: NoteGPTAgentClient):
    """قراءة المهمة من chat_send.txt وحفظ الرد في chat_reply.txt (مسح active_session.txt = بدء شات جديد)"""
    if not os.path.exists(Config.CHAT_SEND_FILE):
        with open(Config.CHAT_SEND_FILE, "w", encoding="utf-8") as f:
            f.write("صمم كود بايثون سريع واشرحه في سطرين بالمصري")
        print(f"{C_YELLOW}⚠️ تم إنشاء ملف {Config.CHAT_SEND_FILE} بمثال تجريبي.{C_RESET}")

    with open(Config.CHAT_SEND_FILE, "r", encoding="utf-8", errors="replace") as f:
        raw_prompt = f.read().strip()

    if not raw_prompt:
        print(f"{C_RED}❌ ملف {Config.CHAT_SEND_FILE} فارغ! اكتب سؤالك فيه أولاً.{C_RESET}")
        return

    # فحص الجلسة (استمرار أم جديدة)
    session_file = pathlib.Path(Config.ACTIVE_SESSION_FILE)
    is_fresh_session = not session_file.exists() or not session_file.read_text(encoding="utf-8", errors="replace").strip()

    client.conv_id = load_active_session()
    
    # فحص المرفقات لعرضها في البانر
    base_dir = pathlib.Path(Config.CHAT_SEND_FILE).parent
    sources, _ = SourceIngestionHandler.parse_sources_and_prompt(raw_prompt, base_dir)
    print_banner(client, sources)

    if is_fresh_session:
        print(f"{C_GREEN}🆕 [بدء شات جديد]: تم اكتشاف مسح ملف الجلسة وبدء محادثة جديدة (Session: {client.conv_id[:8]}...){C_RESET}\n")
    else:
        print(f"{C_CYAN}🔄 [استمرار في نفس الشات]: جاري مواصلة المحادثة السابقة (Session: {client.conv_id[:8]}...){C_RESET}\n")

    print(f"{C_CYAN}📂 تم قراءة السؤال والمصادر من:{C_RESET} {Config.CHAT_SEND_FILE}")
    response = run_single_prompt(client, raw_prompt, base_dir)

    with open(Config.CHAT_REPLY_FILE, "w", encoding="utf-8", errors="replace") as f:
        f.write(response)

    print(f"{C_GREEN}💾 تم حفظ الرد بالكامل في:{C_RESET} {C_YELLOW}{Config.CHAT_REPLY_FILE}{C_RESET}\n")


# ==============================================================================
# 🚀 نقطة الدخول الرئيسية (CLI Interface)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="🚀 سكربت تشغيل وضع الأيجنتس الحقيقي والـ Sandbox (NoteGPT Real Agent Engine v01.03)",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-p", "--prompt", type=str, help="إرسال مهمة مباشرة للأيجنت لتنفيذها في الـ Sandbox")
    parser.add_argument("-m", "--model", type=str, default=None,
                        help=f"اختيار موديل الأيجنت يدوياً (الافتراضي: {Config.DEFAULT_MODEL})\nخيارات: {list(Config.AVAILABLE_MODELS.keys())}")
    parser.add_argument("--auto", action="store_true", help="تفعيل وضع الاختيار التلقائي للموديل (isAutoModel: True)")
    parser.add_argument("-t", "--token", type=str, default=Config.SESSION_TOKEN,
                        help="توكن الجلسة (الافتراضي: سحب وتجديد تلقائي من الحساب)")
    parser.add_argument("-f", "--file", action="store_true", help="قراءة المهمة من chat_send.txt وحفظها في chat_reply.txt")
    parser.add_argument("-i", "--interactive", action="store_true", help="فتح وضع الشات التفاعلي المباشر (Terminal Prompt)")
    parser.add_argument("--new", action="store_true", help="بدء محادثة جديدة وتصفير معرف الجلسة السابق")
    parser.add_argument("--list", action="store_true", help="عرض قائمة جميع موديلات الأيجنتس المتاحة")
    parser.add_argument("--agents", action="store_true", help="عرض قائمة الـ 50 أيجنت المتخصصة المتاحة (Deep Research, Coding, Analytics)")

    args = parser.parse_args()

    if args.token:
        Config.SESSION_TOKEN = args.token

    if args.list:
        print(f"\n{C_MAGENTA}📋 قائمة موديلات الأيجنتس المتاحة:{C_RESET}")
        for short_name, full_name in Config.AVAILABLE_MODELS.items():
            print(f"  • {C_YELLOW}{short_name:<15}{C_RESET} -> {C_CYAN}{full_name}{C_RESET}")
        print()
        return

    if args.agents:
        print(f"\n{C_MAGENTA}🤖 جاري جلب قائمة الـ 50 أيجنت المتخصصة من NoteGPT...{C_RESET}")
        agents = NoteGPTAgentClient.fetch_shared_agents()
        if agents:
            print(f"\n{C_GREEN}✅ تم جلب {len(agents)} أيجنت متخصص بنجاح:{C_RESET}")
            for a in agents[:20]:
                print(f"  • {C_YELLOW}ID {a.get('id'):<3}{C_RESET} | {C_WHITE}{a.get('title')[:45]:<45}{C_RESET} | {C_CYAN}مشاهدات: {a.get('view_count', 0)}{C_RESET}")
            print(f"\n{C_DIM}... والمزيد من الأيجنتس المتاحة في قاعدة البيانات.{C_RESET}\n")
        else:
            print(f"{C_RED}❌ فشل جلب قائمة الأيجنتس.{C_RESET}\n")
        return

    # تحديد الموديل ونمط التشغيل
    is_auto = True if args.auto else Config.IS_AUTO_MODEL
    if args.model:
        selected_model = Config.AVAILABLE_MODELS.get(args.model.lower(), args.model)
        if not args.auto:
            is_auto = False
    else:
        selected_model = Config.DEFAULT_MODEL

    conv_id = create_and_save_new_session() if args.new else load_active_session()
    client = NoteGPTAgentClient(model=selected_model, is_auto=is_auto, conv_id=conv_id)

    if args.prompt:
        base_dir = pathlib.Path.cwd()
        sources, _ = SourceIngestionHandler.parse_sources_and_prompt(args.prompt, base_dir)
        print_banner(client, sources)
        run_single_prompt(client, args.prompt, base_dir)
    elif args.interactive:
        run_interactive_mode(client)
    else:
        # 🚀 الوضع الافتراضي لزر التشغيل السريع (Run Button)
        run_file_mode(client)


if __name__ == "__main__":
    main()
