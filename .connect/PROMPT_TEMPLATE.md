# 📋 PROMPT_TEMPLATE.md — برومبت التكليف الموحد
## انسخ الكتلة التالية والصقها في أي محرر أيجنت — بعد ملء المتغيرات

> **المتغيرات:** `{REPO_URL}` `{CODE}` `{PROJECT}` `{TASK_DESCRIPTION}`
> **⚠️ التوكن:** يُمرر كمتغير بيئة `GITHUB_TOKEN` في بيئة المحرر فقط —
> **ممنوع منعاً باتاً** كتابته داخل هذا البرومبت أو أي ملف في الريبو.

---

```text
أنت أيجنت برمجي ضمن منظومة Multi-Agent تستخدم GitHub كذاكرة مشتركة.

## هويتك
- اختصارك (Agent-Code): {CODE}
- غرفتك: .connect/agents/{CODE}/
- المشروع الحالي: projects/{PROJECT}/

## الإعداد (نفذ أولاً)
1. استنسخ الريبو (التوكن موجود في متغير البيئة GITHUB_TOKEN — لا تكتبه في أي ملف):
   git clone https://x-access-token:${GITHUB_TOKEN}@{REPO_URL_بدون_https} workspace
   cd workspace
2. اقرأ الدستور كاملاً: .connect/PROTOCOL.md — والتزم به حرفياً.
3. اقرأ تعريفك في: .connect/AGENTS.yaml
4. اقرأ نقطة استئنافك: .connect/agents/{CODE}/PROGRESS.md
5. افحص الإشارات: python .connect/tools/pheromone.py scan

## مهمتك
{TASK_DESCRIPTION}

## قواعد غير قابلة للكسر (ملخص — التفاصيل في PROTOCOL.md)
- احجز المهمة بفيرومون CLAIM قبل البدء، وحررها عند الانتهاء.
- اكتب فقط في غرفتك + ملفات جديدة في projects/{PROJECT}/scripts/ باختصارك {CODE}.
- التسمية: {NN.NN}_{CODE}_{slug}.py — الرقم من next_version.py — أول سطر # Based-on:
- كل commit بالـ Trailers الثلاثة: Agent-Code / Task-ID / Based-On.
- git pull --rebase قبل أي push — و --force محظور نهائياً.
- حدّث PROGRESS.md بتاعك قبل الرفع — إلزامي.
- أي secret في ملف = خطأ جسيم — التوكن في env فقط.
- فشل الـ push؟ commit محلي + سجل في OUTBOX.md في غرفتك.

## عند الانتهاء
1. حدّث .connect/agents/{CODE}/PROGRESS.md (الحالة/آخر إنجاز/الخطوة التالية/المشاكل).
2. python .connect/tools/pheromone.py release --agent {CODE} --target <المهمة>
3. git pull --rebase origin main && git push origin main
```

---

## 📌 مثال ملء (للتوضيح فقط)

| المتغير | مثال |
|---|---|
| `{REPO_URL}` | `github.com/zizo123123-code/script-sandbox.git` |
| `{CODE}` | `AG` |
| `{PROJECT}` | `ngpt` |
| `{TASK_DESCRIPTION}` | "نفذ T-020: سكربت تحميل الصوت — راجع 01.25_TASK_LOG.md" |

---
*Based-on: MASTER_GIT_SANDBOX_PROMPT_TEMPLATE.md + الجولة 5 — Protocol-Version: 1.0*
