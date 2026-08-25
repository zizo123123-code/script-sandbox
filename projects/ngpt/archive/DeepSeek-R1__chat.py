import cloudscraper
import json
import uuid
import random
import asyncio
import logging
import time

# استدعاء كلاسات الأساس (يفترض وجودها بناءً على تصميم الفريق)
# عدّل هذا الـ import للـ path الصحيح بتاع BaseProvider
try:
    from providers.base import BaseProvider, ProviderResponse
except ImportError:
    # ⚠️ Placeholder عشان لو الكلاس مش في نفس المسار
    class BaseProvider:
        def __init__(self, **kwargs): pass
    class ProviderResponse:
        def __init__(self, success, content, provider_name, model_name=None, error_message=None):
            self.success = success
            self.content = content
            self.provider_name = provider_name
            self.model_name = model_name
            self.error_message = error_message

logger = logging.getLogger(__name__)

# ==========================================
# دالة لتوليد IP وهمي (Header Spoofing)
# ==========================================
def generate_fake_ip():
    return f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"


class NoteGPTProvider(BaseProvider):
    """
    Provider لـ NoteGPT DeepSeek-R1 ليعمل ضمن الأوركسترا (الفريق).
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url = "https://notegpt.io/api/v2/chat/stream"
        
        # تجهيز الـ scraper مرة واحدة لتقليل الوقت
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'desktop': False}
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """
        الوظيفة اللي بتكلم الـ API بشكل متزامن (Sync) وترجع النص النهائي مع محاولات إعادة عند حدوث 504.
        """
        max_retries = 4
        for attempt in range(1, max_retries + 1):
            anon_user_id = str(uuid.uuid4())
            conv_id = str(uuid.uuid4())
            
            cookies = {
                "anonymous_user_id": anon_user_id,
                "sbox-guid": str(uuid.uuid4())
            }

            fake_ip = generate_fake_ip()

            headers = {
                'Accept': "*/*",
                'Accept-Encoding': "gzip, deflate, br",
                'Content-Type': "application/json",
                'origin': "https://notegpt.io",
                'referer': "https://notegpt.io/ai-chat?hl=ar-EG",
                'accept-language': random.choice(["ar-EG,ar;q=0.9,en-US;q=0.8", "en-US,en;q=0.9"]),
                
                # === هيدرز تمويه الـ IP ===
                'X-Forwarded-For': fake_ip,
                'X-Real-IP': fake_ip,
                'Client-IP': fake_ip
            }

            payload = {
                "message": prompt,
                "language": "auto",
                "model": "TA/deepseek-ai/DeepSeek-R1",
                "tone": "default",
                "length": "moderate",
                "conversation_id": conv_id,
                "image_urls": [],
                "chat_mode": "deep_think"
            }

            # إعادة إنشاء scraper جديد بمتصفح عشوائي
            is_desktop = (attempt % 2 == 0)
            scraper = cloudscraper.create_scraper(
                browser={'browser': 'chrome', 'platform': 'windows' if is_desktop else 'android', 'desktop': is_desktop}
            )

            try:
                response = scraper.post(
                    self.url, json=payload, headers=headers, cookies=cookies, stream=True, timeout=45
                )
                
                if response.status_code == 200:
                    full_text = ""
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8', errors='ignore')
                            if decoded_line.startswith("data: "):
                                json_str = decoded_line[6:] 
                                try:
                                    data = json.loads(json_str)
                                    if data.get("done"):
                                        break
                                    
                                    # تجميع النص فقط بدون التفكير
                                    text = data.get("text", "")
                                    if text:
                                        full_text += text
                                        
                                except json.JSONDecodeError:
                                    pass
                    
                    if full_text.strip():
                        return full_text.strip()
                    
                logger.warning(f"⚠️ NoteGPT Attempt {attempt}/{max_retries} Failed: {response.status_code}")
                if attempt < max_retries:
                    time.sleep(2)

            except Exception as e:
                logger.warning(f"⚠️ NoteGPT Connection Error (Attempt {attempt}): {e}")
                if attempt < max_retries:
                    time.sleep(2)

        # 🚀 [FALLBACK]: لو NoteGPT موصلش/مردش بسبب الـ 504، نستخدم DeepSeek المباشر
        try:
            logger.info("🔄 [Fallback] جاري استدعاء DeepSeek المباشر...")
            import pathlib
            import importlib.util
            ds_path = pathlib.Path(__file__).parent / "deepseek_chat.py"
            if ds_path.exists():
                spec = importlib.util.spec_from_file_location("deepseek_chat_mod", ds_path)
                ds_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(ds_mod)
                if hasattr(ds_mod, "ask_deepseek"):
                    fallback_res = ds_mod.ask_deepseek(prompt)
                    if fallback_res:
                        return fallback_res
        except Exception as fb_err:
            logger.warning(f"⚠️ DeepSeek Fallback Error: {fb_err}")

        return ""

    async def ask(self, prompt: str, **kwargs) -> ProviderResponse:
        """
        شريان الحياة مع الفريق (Orchestrator). 
        يجب أن يعيد ProviderResponse ولا يعمل block للـ event loop.
        """
        logger.info(f"[NoteGPT] جاري توليد رد لسؤال: {prompt[:30]}...")
        
        # بننادي الكود الـ Sync في خلفية عشان مانعطلش الفريق كله
        start_time = time.time()
        result = await asyncio.to_thread(self.generate, prompt, **kwargs)
        elapsed = time.time() - start_time
        
        if result:
            logger.info(f"[NoteGPT] ✅ نجح في {elapsed:.2f}s")
            return ProviderResponse(
                success=True,
                content=result,
                provider_name="notegpt",
                model_name="DeepSeek-R1"
            )
        else:
            logger.error(f"[NoteGPT] ❌ فشل في جلب الرد")
            return ProviderResponse(
                success=False,
                content="عذراً مش قادر أتواصل مع الـ سيرفر حالياً",
                provider_name="notegpt",
                error_message="لم يتم استلام رد من NoteGPT API"
            )

# ═══════════════════════════════════════════════════════════════════════
#  تشغيل كسكربت منفصل أو من المايسترو (team_runner.py)
# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys as _sys
    import pathlib as _p

    # إصلاح طباعة الإيموجي على ويندوز
    if _sys.platform == "win32":
        try:
            _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

    # قراءة السؤال من chat_send.txt (نفس نمط باقي الفريق)
    _chat_file = _p.Path(__file__).parent / "chat_send.txt"
    _question = ""
    if _chat_file.exists():
        _question = _chat_file.read_text(encoding="utf-8").strip()

    if not _question:
        print("⚠️ ملف chat_send.txt فاضي أو مش موجود!")
        _sys.exit(1)

    provider = NoteGPTProvider()
    result = provider.generate(_question)

    if result:
        print(result)
    else:
        print("❌ فشل الحصول على رد من NoteGPT / DeepSeek-R1")
