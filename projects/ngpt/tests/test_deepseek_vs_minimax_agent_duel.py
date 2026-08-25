#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
⚔️ DEEPSEEK-V4-FLASH vs MINIMAX-M3 — AGENT SANDBOX PARALLEL DUEL ARENA
================================================================================
📌 الوصف:
    حلبة مقارنة متوازية وفورية بنسبة 100% بين أقوى موديلين في وضع الأيجنتس والـ Sandbox:
    1. 🤖 DeepSeek V4 Flash (المحرك السريع للتحليل المعماري والأدوات)
    2. ⚡ MiniMax M3 (محرك الأكواد المعقدة والمنطق البرمجي)

✨ المميزات:
    • تشغيل متزامن 100% في نفس اللحظة عبر ThreadPoolExecutor.
    • وضع الأيجنتس الحقيقي مع بيئة تشغيل Sandbox معزولة (chat_mode: 'agent').
    • رصد وسحب التفكير المنطقي لايف (Reasoning Trace) للأول والثاني.
    • مقارنة جودة الأكواد وخلوها من التخمين والهبد البرمجي.
    • حفظ التقرير والمقارنة جنباً إلى جنب في chat_reply.txt.

================================================================================
"""

import sys
import io
import os
import time
import json
import uuid
import random
import pathlib
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Generator, Dict, Any

# ضبط مخرجات التيرمينال لـ UTF-8 على أنظمة ويندوز
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.platform == "win32":
    os.system("chcp 65001 > nul")

# استيراد مكتبة تخطي الحمايات (Cloudscraper)
try:
    import cloudscraper
except ImportError:
    print("❌ مكتبة cloudscraper غير مثبتة! قم بتثبيتها عبر: pip install cloudscraper")
    sys.exit(1)

# استيراد ألوان التيرمينال النيونية (Colorama)
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
# ⚙️ كلاس الإعدادات الموحد (SSOT Config)
# ==============================================================================
class Config:
    """إعدادات حلبة المقارنة المتوازية بين DeepSeek و MiniMax"""
    BASE_DIR = pathlib.Path(__file__).resolve().parent
    CHAT_SEND_FILE = BASE_DIR / "chat_send.txt"
    CHAT_REPLY_FILE = BASE_DIR / "chat_reply.txt"

    BASE_URL: str = "https://notegpt.io/api/v2/chat/stream"
    AGENT_REFERER: str = "https://notegpt.io/ai-agent"
    ORIGIN_URL: str = "https://notegpt.io"
    AUTH_LOGIN_URL: str = "https://notegpt.io/api/v1/auth/email/login"

    # الموديلان المستهدفان في حلبة المبارزة
    MODEL_DEEPSEEK: Dict[str, str] = {
        "id": "deepseek-v4-flash",
        "name": "🤖 DeepSeek V4 Flash",
        "color": C_CYAN,
        "desc": "محرك الأيجنتس السريع للتحليل المعماري والـ Sandbox",
    }
    
    MODEL_MINIMAX: Dict[str, str] = {
        "id": "minimax-m3",
        "name": "⚡ MiniMax M3",
        "color": C_YELLOW,
        "desc": "محرك الأكواد والمنطق البرمجي المتقدم",
    }

    # السؤال المعياري الناري لكشف العمق وتفادي التخمين
    DEFAULT_PROMPT: str = (
        "صمم واكتب كود بايثون متكامل لخوارزمية Distributed Sliding Window Rate Limiter "
        "مع معالجة الـ Concurrency والـ Race Conditions باستخدام Redis Lua Scripts، "
        "واشرح ليه الخوارزمية دي أحسن من Token Bucket بالمصري مع توضيح التعقيد الزمني والمكاني."
    )

    REQUEST_TIMEOUT: int = 60

    # بيانات الحساب المسجل لسحب التوكن الحي
    EMAIL: str = "r2ewt31t4354@msp.mailings.live"
    PASSWORD: str = "GPt2sjUZwFKf#vd"
    SESSION_TOKEN: str = ""


# ==============================================================================
# 🛠️ الدوال المساعدة وتوليد الهويات
# ==============================================================================
def generate_fake_ip() -> str:
    """توليد IP وهمي لتمويه الهيدرز لكل طلب"""
    return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"


def print_duel_banner(prompt: str):
    """طباعة بانر نيون فاخر لبدء حلبة المقارنة المتوازية"""
    print(f"\n{C_MAGENTA}╔════════════════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_MAGENTA}║  ⚔️ DEEPSEEK-V4-FLASH vs MINIMAX-M3 — AGENT SANDBOX PARALLEL DUEL ARENA           ║{C_RESET}")
    print(f"{C_MAGENTA}║  📌 اختبار العمق البرمجي والـ Reasoning في بيئة Sandbox معزولة بالتوازي 100%        ║{C_RESET}")
    print(f"{C_MAGENTA}╚════════════════════════════════════════════════════════════════════════════════════╝{C_RESET}")
    print(f"  {C_CYAN}🤖 الموديل الأول :{C_RESET} {C_WHITE}{Config.MODEL_DEEPSEEK['name']}{C_RESET} ({C_DIM}{Config.MODEL_DEEPSEEK['desc']}{C_RESET})")
    print(f"  {C_YELLOW}⚡ الموديل الثاني:{C_RESET} {C_WHITE}{Config.MODEL_MINIMAX['name']}{C_RESET} ({C_DIM}{Config.MODEL_MINIMAX['desc']}{C_RESET})")
    print(f"  {C_GREEN}📝 المهمة        :{C_RESET} {C_WHITE}{prompt[:80]}...{C_RESET}")
    print(f"{C_MAGENTA}────────────────────────────────────────────────────────────────────────────────────{C_RESET}\n")


# ==============================================================================
# 🧠 كلاس الاتصال بالأيجنت (Agent Worker)
# ==============================================================================
class AgentWorker:
    """منفذ طلبات الأيجنت المستقل لكل موديل"""

    def __init__(self, model_info: Dict[str, str]):
        self.model_id = model_info["id"]
        self.model_name = model_info["name"]
        self.color = model_info["color"]
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
        )
        self.conv_id = str(uuid.uuid4())
        self.anon_user_id = str(uuid.uuid4())
        self.sbox_guid = str(uuid.uuid4())
        self.cookies = {
            "anonymous_user_id": self.anon_user_id,
            "sbox-guid": self.sbox_guid
        }

    def ensure_login(self) -> bool:
        """تسجيل الدخول وسحب التوكن الحي لو غير موجود"""
        if Config.SESSION_TOKEN:
            return True
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
                token = r.json().get("data", {}).get("access_token")
                if token:
                    Config.SESSION_TOKEN = token
                    self.cookies["token"] = token
                    self.cookies["access_token"] = token
                    return True
        except Exception:
            pass
        return False

    def _build_headers(self) -> Dict[str, str]:
        """بناء الهيدرات المستقلة"""
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

    def _create_chat_session(self, prompt: str):
        """المرحلة الأولى: إنشاء الجلسة في قاعدة بيانات السجل ليظهر العنوان في المتصفح فوراً"""
        try:
            now_ms = int(time.time() * 1000)
            payload = {
                "source": "agent",
                "content": {
                    "title": prompt[:100],
                    "updateTime": now_ms,
                    "chat_list": [
                        {
                            "label": prompt[:100],
                            "question": prompt,
                            "answer": [""],
                            "reasoning": [{"startedAt": None, "endedAt": None, "reasoning": "", "thinkingSeconds": 0}],
                            "blocks": [],
                            "isStreaming": True,
                            "isInterrupted": False,
                            "generatedFiles": [],
                            "conversation_id": self.conv_id,
                            "created_at": now_ms,
                            "modelValue": self.model_id,
                            "isAutoModel": True,
                            "isStopped": False
                        }
                    ]
                }
            }
            headers = self._build_headers()
            headers['content-type'] = 'application/json; charset=UTF-8'
            self.scraper.post("https://notegpt.io/api/v2/ai-chat", json=payload, headers=headers, cookies=self.cookies, timeout=10)
        except Exception:
            pass

    def _finalize_chat_session(self, prompt: str, reasoning: str, text: str):
        """المرحلة الثانية: حفظ الرد الكامل والـ Reasoning في قاعدة بيانات السجل"""
        try:
            now_ms = int(time.time() * 1000)
            now_sec = int(time.time())
            blocks = []
            if reasoning:
                blocks.append({"type": "reasoning", "content": reasoning})
            if text:
                blocks.append({"type": "text", "content": text})
            blocks.append({"type": "credit_usage", "content": 1})

            payload = {
                "id": self.conv_id,
                "content": {
                    "question": prompt,
                    "type": "text",
                    "status": "finish",
                    "source": "agent",
                    "created_at": now_sec,
                    "updated_at": now_sec,
                    "chat_list": [
                        {
                            "label": prompt[:100],
                            "question": prompt,
                            "answer": [text],
                            "blocks": blocks,
                            "isStreaming": False,
                            "isInterrupted": False,
                            "generatedFiles": [],
                            "conversation_id": self.conv_id,
                            "created_at": now_ms,
                            "modelValue": self.model_id,
                            "isAutoModel": True,
                            "isStopped": False,
                            "creditsUsed": 1
                        }
                    ]
                }
            }
            headers = self._build_headers()
            headers['content-type'] = 'application/json; charset=UTF-8'
            self.scraper.put("https://notegpt.io/api/v2/ai-chat", json=payload, headers=headers, cookies=self.cookies, timeout=10)
        except Exception:
            pass

    def execute_prompt(self, prompt: str) -> Dict[str, Any]:
        """تنفيذ المهمة وسحب الرد والتفكير والـ Sandbox وحفظها في قاعدة بيانات السجل"""
        self.ensure_login()
        if Config.SESSION_TOKEN:
            self.cookies["token"] = Config.SESSION_TOKEN
            self.cookies["access_token"] = Config.SESSION_TOKEN
            
        # 1. إنشاء الجلسة في قاعدة بيانات السايدبار
        self._create_chat_session(prompt)
        
        headers = self._build_headers()
        payload = {
            "message": prompt,
            "model": self.model_id,
            "language": "auto",
            "tone": "default",
            "length": "moderate",
            "conversation_id": self.conv_id,
            "chat_mode": "agent",
            "isAutoModel": True
        }

        start_time = time.time()
        sandbox_steps = []
        reasoning_chunks = []
        text_chunks = []
        error_msg = None

        try:
            r = self.scraper.post(
                Config.BASE_URL,
                json=payload,
                headers=headers,
                cookies=self.cookies,
                stream=True,
                timeout=Config.REQUEST_TIMEOUT
            )

            if r.status_code != 200:
                error_msg = f"خطأ سيرفر: {r.status_code}"
            else:
                for line in r.iter_lines():
                    if not line:
                        continue
                    dec = line.decode('utf-8', errors='replace').strip()
                    
                    if dec.startswith("{") and dec.endswith("}"):
                        try:
                            err_data = json.loads(dec)
                            if err_data.get("code") and err_data.get("code") != 100000:
                                error_msg = f"{err_data.get('message')} (كود {err_data.get('code')})"
                                break
                        except Exception:
                            pass

                    if dec.startswith("data: "):
                        data_part = dec[6:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            ev = json.loads(data_part)
                            etype = ev.get("type")
                            if etype == "prepare_env":
                                sandbox_steps.append(ev.get("step"))
                            elif etype == "reasoning" and ev.get("reasoning"):
                                reasoning_chunks.append(ev.get("reasoning"))
                            elif etype == "text" and ev.get("text"):
                                text_chunks.append(ev.get("text"))
                        except Exception:
                            pass

        except Exception as e:
            error_msg = str(e)

        elapsed = round(time.time() - start_time, 2)
        full_reasoning = "".join(reasoning_chunks)
        full_text = "".join(text_chunks)

        # 2. حفظ الرد النهائي بالكامل في قاعدة بيانات سجل الموقع (Recents Sidebar)
        if not error_msg and (full_text or full_reasoning):
            self._finalize_chat_session(prompt, full_reasoning, full_text)

        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "color": self.color,
            "elapsed": elapsed,
            "sandbox_steps": sandbox_steps,
            "reasoning": full_reasoning,
            "text": full_text,
            "error": error_msg,
            "conv_id": self.conv_id
        }


def global_login() -> str:
    """تسجيل الدخول المركزي المسبق وسحب التوكن الحي قبل تشغيل الثريدات المتوازية"""
    if Config.SESSION_TOKEN:
        return Config.SESSION_TOKEN
    if not Config.EMAIL or not Config.PASSWORD:
        return ""
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'android', 'desktop': False})
        headers = {
            'Accept': "*/*",
            'Content-Type': "application/json; charset=UTF-8",
            'origin': Config.ORIGIN_URL,
            'referer': f"{Config.ORIGIN_URL}/login",
        }
        payload = {"email": Config.EMAIL, "password": Config.PASSWORD}
        r = scraper.post(Config.AUTH_LOGIN_URL, json=payload, headers=headers, timeout=10)
        if r.status_code == 200:
            token = r.json().get("data", {}).get("access_token")
            if token:
                Config.SESSION_TOKEN = token
                return token
    except Exception:
        pass
    return ""


def extract_and_save_sandbox_files(reasoning: str, answer: str, task_name: str, model_tag: str, base_dir: pathlib.Path = None) -> list:
    """
    📥 Auto Sandbox Exporter (Parallel Duel Edition):
    استخراج وتحميل كافة الملفات المنشأة داخل بيئة الـ Linux Sandbox
    وحفظها في مجلد محلي منظم لكل موديل باسم المهمة والتوقيت.
    """
    import re
    if base_dir is None:
        base_dir = Config.BASE_DIR / "agent_output"
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in task_name[:25] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    folder_name = f"{timestamp}_{safe_name}_{model_tag}" if safe_name else f"{timestamp}_{model_tag}"
    task_dir = base_dir / folder_name
    task_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    combined_text = (reasoning or "") + "\n\n" + (answer or "")
    
    # 1. استخراج ملفات بصيغة JSON tool calls {"file_path": "...", "content": "..."}
    file_matches = re.findall(r'\{[^{}]*"file_path":\s*"([^"]+)",\s*"content":\s*"((?:\\.|[^"\\])*)"', combined_text)
    for path_str, content_escaped in file_matches:
        fname = pathlib.Path(path_str).name
        try:
            content_decoded = json.loads(f'"{content_escaped}"')
        except Exception:
            content_decoded = content_escaped.encode().decode('unicode-escape', errors='replace')
        fpath = task_dir / fname
        with open(fpath, "w", encoding="utf-8", errors="replace") as f:
            f.write(content_decoded)
        saved_files.append((fname, fpath, len(content_decoded)))
        
    # 2. استخراج ملفات بنمط Markdown blocks التي تبدأ باسم ملف
    if not saved_files:
        code_blocks = re.findall(r'```(?:python|markdown|bash|json|html|css|javascript|ts)?\s*(?:#|\/\*|"""|\/\/)?\s*([a-zA-Z0-9_\-\.]+\.(?:py|md|txt|json|sh|js|ts|html|css))\s*[\r\n]+(.*?)\s*```', combined_text, re.DOTALL)
        for fname, block in code_blocks:
            fpath = task_dir / fname
            with open(fpath, "w", encoding="utf-8", errors="replace") as f:
                f.write(block)
            saved_files.append((fname, fpath, len(block)))
            
    # 3. لو لم نجد أسماء ملفات واضحة ووجدنا كود بايثون أو ماركداون رئيسي
    if not saved_files:
        raw_blocks = re.findall(r'```(python|markdown|bash|json)?\s*(.*?)\s*```', combined_text, re.DOTALL)
        for idx, (lang, block) in enumerate(raw_blocks):
            ext = "py" if lang == "python" else ("md" if lang == "markdown" else ("sh" if lang == "bash" else "txt"))
            fname = f"code_solution_{idx+1}.{ext}"
            fpath = task_dir / fname
            with open(fpath, "w", encoding="utf-8", errors="replace") as f:
                f.write(block)
            saved_files.append((fname, fpath, len(block)))
            
    if saved_files:
        print(f"  {C_GREEN}📥 [Auto Sandbox Exporter - {model_tag}]: تم تنزيل {len(saved_files)} ملف محلياً في: {task_dir}{C_RESET}")
            
    return saved_files


# ==============================================================================
# 🚀 إدارة المقارنة المتوازية (Parallel Duel Engine)
# ==============================================================================
def run_duel(prompt: str) -> Dict[str, Dict[str, Any]]:
    """إرسال المهمة للموديلين في نفس اللحظة بالتوازي وجمع النتائج وتنزيل ملفات الـ Sandbox"""
    print_duel_banner(prompt)
    
    # ضمان وجود توكن جلسة نشط قبل البدء
    global_login()

    print(f"{C_MAGENTA}🚀 [بدء البث المتوازي]: جاري إرسال المهمة لموديل DeepSeek V4 وموديل MiniMax M3 بالتوازي...{C_RESET}\n")

    workers = [
        AgentWorker(Config.MODEL_DEEPSEEK),
        AgentWorker(Config.MODEL_MINIMAX)
    ]

    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_worker = {executor.submit(w.execute_prompt, prompt): w for w in workers}
        for future in as_completed(future_to_worker):
            res = future.result()
            results[res["model_id"]] = res
            color = res["color"]
            print(f"{color}🏁 انتهى {res['model_name']} في {res['elapsed']} ثانية!{C_RESET}")

    print(f"\n{C_MAGENTA}════════════════════════════════════════════════════════════════════════════════════{C_RESET}")
    print(f"{C_MAGENTA}                      📊 نتائج المقارنة المتوازية والتحليل البرمجي                     {C_RESET}")
    print(f"{C_MAGENTA}════════════════════════════════════════════════════════════════════════════════════{C_RESET}\n")

    # عرض نتيجة DeepSeek واستخراج ملفاته
    d_res = results.get("deepseek-v4-flash", {})
    print(f"{C_CYAN}╔════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_CYAN}║  🤖 {d_res.get('model_name', 'DeepSeek')} (الوقت: {d_res.get('elapsed')}s)                       ║{C_RESET}")
    print(f"{C_CYAN}╚════════════════════════════════════════════════════════════════════════╝{C_RESET}")
    if d_res.get("error"):
        print(f"{C_RED}❌ خطأ: {d_res['error']}{C_RESET}\n")
    else:
        if d_res.get("reasoning"):
            print(f"{C_MAGENTA}🧠 [تفكير DeepSeek المنطقي]:{C_RESET}\n{C_DIM}{d_res['reasoning'][:400]}...{C_RESET}\n")
        print(f"{C_CYAN}💻 [الحل البرمجي والكود]:{C_RESET}\n{d_res.get('text')}\n")
        extract_and_save_sandbox_files(d_res.get("reasoning"), d_res.get("text"), prompt, "deepseek_v4")

    print(f"{C_MAGENTA}────────────────────────────────────────────────────────────────────────────────────{C_RESET}\n")

    # عرض نتيجة MiniMax واستخراج ملفاته
    m_res = results.get("minimax-m3", {})
    print(f"{C_YELLOW}╔════════════════════════════════════════════════════════════════════════╗{C_RESET}")
    print(f"{C_YELLOW}║  ⚡ {m_res.get('model_name', 'MiniMax')} (الوقت: {m_res.get('elapsed')}s)                         ║{C_RESET}")
    print(f"{C_YELLOW}╚════════════════════════════════════════════════════════════════════════╝{C_RESET}")
    if m_res.get("error"):
        print(f"{C_RED}❌ خطأ: {m_res['error']}{C_RESET}\n")
    else:
        if m_res.get("reasoning"):
            print(f"{C_MAGENTA}🧠 [تفكير MiniMax المنطقي]:{C_RESET}\n{C_DIM}{m_res['reasoning'][:400]}...{C_RESET}\n")
        print(f"{C_YELLOW}💻 [الحل البرمجي والكود]:{C_RESET}\n{m_res.get('text')}\n")
        extract_and_save_sandbox_files(m_res.get("reasoning"), m_res.get("text"), prompt, "minimax_m3")

    # حفظ النتائج في chat_reply.txt
    save_content = (
        f"# ⚔️ نتائج المبارزة المتوازية: DeepSeek V4 vs MiniMax M3\n\n"
        f"## 📝 المهمة:\n{prompt}\n\n"
        f"---\n\n"
        f"## 🤖 DeepSeek V4 Flash ({d_res.get('elapsed')}s):\n"
        f"{d_res.get('text')}\n\n"
        f"---\n\n"
        f"## ⚡ MiniMax M3 ({m_res.get('elapsed')}s):\n"
        f"{m_res.get('text')}\n"
    )
    with open(Config.CHAT_REPLY_FILE, "w", encoding="utf-8", errors="replace") as f:
        f.write(save_content)
    print(f"\n{C_GREEN}💾 تم حفظ تقرير المقارنة المتوازية بالكامل في: {Config.CHAT_REPLY_FILE}{C_RESET}\n")

    return results


# ==============================================================================
# 🎯 دوال التشغيل الرئيسية (CLI)
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="⚔️ حلبة المقارنة المتوازية لموديلات الأيجنتس: DeepSeek V4 vs MiniMax M3",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-p", "--prompt", type=str, help="إرسال سؤال أو مسألة برمجية محددة للموديلين بالتوازي")
    parser.add_argument("-f", "--file", action="store_true", help="قراءة السؤال من chat_send.txt وحفظ المقارنة في chat_reply.txt")

    args = parser.parse_args()

    if args.prompt:
        run_duel(args.prompt)
    elif args.file:
        if not os.path.exists(Config.CHAT_SEND_FILE):
            with open(Config.CHAT_SEND_FILE, "w", encoding="utf-8") as f:
                f.write(Config.DEFAULT_PROMPT)
        with open(Config.CHAT_SEND_FILE, "r", encoding="utf-8", errors="replace") as f:
            p = f.read().strip()
        run_duel(p if p else Config.DEFAULT_PROMPT)
    else:
        # تشغيل السؤال المعياري الناري مباشرة
        run_duel(Config.DEFAULT_PROMPT)


if __name__ == "__main__":
    main()
