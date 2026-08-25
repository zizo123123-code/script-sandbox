# 🤖 NoteGPT Real Agent Sandbox Engine (v01.05)
> **Pure Requests • Cloud Daytona Linux Sandbox • Native Multi-Modal Files • Zero Browser Overhead**

[![Python Version](https://img.shields.io/badge/Python-3.9+-blue.svg?style=flat-square&logo=python)](https://python.org)
[![Cloud Daytona Sandbox](https://img.shields.io/badge/Sandbox-Daytona%20Linux%20Cloud-orange.svg?style=flat-square)](https://daytona.io)
[![Pure Requests](https://img.shields.io/badge/Engine-Cloudscraper%20%2B%20Pure%20Requests-green.svg?style=flat-square)](https://github.com/VeNoMouS/cloudscraper)
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=flat-square)](LICENSE)

---

## 📖 نظرة عامة (Overview)

محرك ذكي وخفيف بنسبة 100% لتشغيل بيئة الأيجنتس السحابية (**NoteGPT Agent Sandbox Engine**) عبر **Pure Requests** دون الحاجة لفتح أي متصفحات ثقيلة (Selenium/Playwright) أو استهلاك موارد الجهاز.

السكربت يتصل مباشرة ببيئة **Daytona Linux Sandbox** المعزولة سحابياً، وينفذ الأكواد، ويفحص الصور بـ Vision، ويفرغ فيديوهات YouTube، ويقوم بتدوير الـ IP ومعرفات الـ Cookies تلقائياً مع تنزيل كافة المشاريع المصممة محلياً.

---

## ✨ المميزات الرئيسية (Key Features)

- 🚀 **تشغيل سحابي حقيقي (Daytona Linux Sandbox):**
  - تنفيذ كامل لأوامر الـ Bash وتثبيت الحزم (`pip`, `npm`, `apt`).
  - تشغيل كود بايثون واختباره واستخراج مخرجاته مباشرة.
- 📁 **مجلد الإسقاط السريع الذكي (`chat_attachments/`):**
  - اسحب أي صورة أو ملف كود بالماوس للمجلد واضغط `Run` — يتم التقاطه وبناء مصفوفة `files` الأصلية فوراً.
  - فحص أبعاد وبيانات الصور وتحليلها بأداة `image_recognition` الأصلية.
- 🎥 **دعم الوسائط والروابط الخارجية (YouTube & Web Tools):**
  - دعم تفريغ وتلخيص مقاطع اليوتيوب وصفحات الويب عبر أدوات `fetch_url` و `web_search`.
- 🕒 **مزامنة تاريخ وسجل المتصفح (`fileInfos` History Sync):**
  - توثيق المحادثات والمرفقات تلقائياً في تاريخ المتصفح عبر `POST /api/v2/ai-chat` و `PUT /api/v2/ai-chat`.
- 🛡️ **تدوير الـ IP ومعرفات الجلسة الذكي (Dynamic Identity Rotation):**
  - توليد عنوان IP وهمي جديد مع كل سؤال (`X-Forwarded-For`, `X-Real-IP`, `Client-IP`).
  - الحفاظ التام على نفس معرّف الجلسة (`conversation_id`) لتراكم السياق.
- 📥 **تنزيل وحفظ ملفات الساندبوكس تلقائياً (Auto CDN Exporter):**
  - تنزيل كافة ملفات الأكواد المنشأة داخل الساندبوكس وحفظها في `agent_output/`.
- 🧹 **تدوير السجل بنظام الكاميرات FIFO:**
  - حفظ آخر 10 مشاريع فقط ومسح الأقدم تلقائياً لمنع تراكم الملفات.

---

## 🏗️ هيكل المشروع (Project Directory Structure)

```text
script-sandbox/
├── 🚀 01.05_notegpt_agent_mode.py        # المحرك الرئيسي الأحدث (Native Files & History Sync)
├── ⚡ test_notegpt_agent_mode.py         # سكريبت التشغيل السريع الموحد لزر Run
├── 🧠 DeepSeek-R1__chat.py               # عميل DeepSeek R1 المباشر
├── ⚔️ test_deepseek_vs_minimax_agent_duel.py # اختبار مقارنة الموديلات والساندبوكس
├── 📦 versions_archive/                  # أرشيف منظم للإصدارات السابقة (v01.02, v01.03, v01.04)
├── 📁 har_archives/                      # أرشيف تدفقات الشبكة وتحليلات الـ HAR
├── 📂 chat_attachments/                  # مجلد إسقاط الصور والمرفقات السريع
├── 📥 agent_output/                      # مجلد حفظ ملفات الساندبوكس المنزلة محلياً
├── 📋 notegpt_catalog.json               # كتالوج الموديلات والأيجنتس المكتشفة
├── 📄 chat_send.txt                      # ملف كتابة المهام للمحرر
├── 📄 chat_reply.txt                     # ملف استقبال الإجابات والردود
├── 📚 NOTEGPT_AGENT_SANDBOX_MASTER_DOCUMENTATION.md # التوثيق الشامل
├── 📦 requirements.txt                   # مكتبات البايثون المطلوبة
└── 🛡️ .gitignore                         # استثناء ملفات الكاش والمؤقتة
```

---

## 🤖 الموديلات المدعومة (Supported Models)

| الاسم المختصر | الموديل في NoteGPT API | الوصف والتخصص |
| :--- | :--- | :--- |
| `deepseek` | `deepseek-v4-flash` | 🐳 الموديل الافتراضي السريع لكتابة وتجربة الأكواد |
| `minimax` | `minimax-m3` | ⚡ موديل MiniMax القوي في الساندبوكس وتحليل الملفات |
| `glm` | `glm-5.2` | 🔮 موديل GLM الصيني المتقدم |
| `r1` | `TA/deepseek-ai/DeepSeek-R1` | 🧠 موديل التفكير العميق الاستدلالي |
| `gpt4o` | `gpt-4o` | 🟢 موديل OpenAI متعدد الوسائط |
| `claude-fable` | `claude-fable-5` | 🎭 موديل كلود فابل للإبداع والتحليل |

---

## 🚀 التثبيت والتشغيل (Quick Start)

### 1. تثبيت المتطلبات:
```bash
pip install -r requirements.txt
```

### 2. طرق التشغيل:

#### ⚡ أ. زر التشغيل السريع من المحرر (Run Button / File Mode):
1. اكتب سؤالك في ملف `chat_send.txt`.
2. (اختياري) اسحب صورتك أو ملفك إلى مجلد `chat_attachments/`.
3. اضغط على زر **Run** لتشغيل `01.05_notegpt_agent_mode.py` أو `test_notegpt_agent_mode.py`.
4. تجد الرد كاملاً في `chat_reply.txt` والملفات في `agent_output/`.

#### 💻 ب. عبر سطر الأوامر (CLI Prompt):
```bash
# تنفيذ مهمة نصية سريعة
python 01.05_notegpt_agent_mode.py -p "صمم كود بايثون لآلة حاسبة واشرحه"

# تنفيذ مهمة مع تحديد الموديل
python 01.05_notegpt_agent_mode.py -m minimax -p "حلل بيانات المشروع واكتب تقرير"

# تفريغ وتلخيص فيديو يوتيوب
python 01.05_notegpt_agent_mode.py -p "https://www.youtube.com/watch?v=F9IiYZoWBr0 لخص النقاط العملية"
```

#### 💬 ج. وضع الشات التفاعلي (Interactive Mode):
```bash
python 01.05_notegpt_agent_mode.py -i
```

---

## 📊 بطاقة التقرير النهائي (Execution Report Preview)

```text
════════════════════════════════════════════════════════════════════
 📊 ملخص تقرير تنفيذ المهمة (Execution Summary Report)
────────────────────────────────────────────────────────────────────
  🎯 وضع التشغيل     : 🌸 وضع الأيجنتس السحابي (Cloud Linux Sandbox 🤖)
  🤖 الموديل         : 🐳 [DeepSeek V4 Flash] (Manual 🎯)
  📝 عنوان المهمة    : "اشرحلي الصورة المرفقة في 3 نقط بالمصري"
  🆔 معرّف الجلسة    : 49d544fc-e3b3-405e-a45c-761270f083cf
  🛡️ الـ IP المستخدم  : 131.156.21.56
  📎 المرفقات والوسائط: ✅ مفعّل (1 مرفق): 🖼️ 1 صور (Vision & Native Files)
  🛠️ أدوات الساندبوكس : ✅ تم استدعاء (1 أداة): 👁️ Image Recognition
────────────────────────────────────────────────────────────────────
  ⏱️  زمن الاستجابة   : 1.80 ثانية  |  💳 الكريديت المستهلك: 1 Credits
  🔄 جولات الساندبوكس : جولة واحدة (Turn 1) ✅  |  📡 استئناف الستريم: 1 استئناف 🔄
  🛡️ التعافي الذاتي  : ⚡ تم التنشيط والتعافي الذاتي بنجاح (Self-Healing Active)
  💳 حالة الرصيد     : ✅ رصيد الحساب كافي ومتاح (لم ينفد)
────────────────────────────────────────────────────────────────────
  📦 ملفات الساندبوكس: تم تسليم الإجابة وتنزيل الملفات في agent_output/
════════════════════════════════════════════════════════════════════
```

---

## 📜 الترخيص (License)
هذا المشروع مرخص تحت رخصة **MIT**.
