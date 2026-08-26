# 🧬 DNA_TREE.md — شجرة جينوم مشروع `ngpt`
> تتولد آلياً بـ `dna_tree.py` — آخر توليد: 2026-08-26

```mermaid
graph TD
  Nngpt_01_02_LEGACY_agent_mode["01.02_LEGACY_agent-mode 🟢<br/>الأساس — تشغيل وضع الأيجنتس الحقيقي فقط "]
  Nngpt_01_03_LEGACY_agent_mode["01.03_LEGACY_agent-mode 🟢<br/>إضافة المصادر المتعددة (روابط + ملفات) ل"]
  Nngpt_01_02_LEGACY_agent_mode --> Nngpt_01_03_LEGACY_agent_mode
  Nngpt_01_04_LEGACY_agent_mode["01.04_LEGACY_agent-mode 🟢<br/>Auto Drop-Folder + تدوير IP نقي"]
  Nngpt_01_03_LEGACY_agent_mode --> Nngpt_01_04_LEGACY_agent_mode
  Nngpt_01_05_LEGACY_agent_mode["01.05_LEGACY_agent-mode 🟢<br/>مطابقة كاملة مع HAR الأخير: Native Files"]
  Nngpt_01_04_LEGACY_agent_mode --> Nngpt_01_05_LEGACY_agent_mode
  Nngpt_01_06_LEGACY_agent_mode["01.06_LEGACY_agent-mode 🟢<br/>Smart Git Rebase + Live Browser Sidebar "]
  Nngpt_01_05_LEGACY_agent_mode --> Nngpt_01_06_LEGACY_agent_mode
  style Nngpt_01_02_LEGACY_agent_mode fill:#0d3321,stroke:#22c55e,color:#dcfce7
  style Nngpt_01_03_LEGACY_agent_mode fill:#0d3321,stroke:#22c55e,color:#dcfce7
  style Nngpt_01_04_LEGACY_agent_mode fill:#0d3321,stroke:#22c55e,color:#dcfce7
  style Nngpt_01_05_LEGACY_agent_mode fill:#0d3321,stroke:#22c55e,color:#dcfce7
  style Nngpt_01_06_LEGACY_agent_mode fill:#0d3321,stroke:#22c55e,color:#dcfce7
```

| الملف | الجيل | المؤلف | الحالة | الطفرة |
|---|---|---|---|---|
| `01.02_notegpt_agent_mode.py` | 1 | LEGACY | 🟢 | الأساس — تشغيل وضع الأيجنتس الحقيقي فقط عبر Pure Requests |
| `01.03_notegpt_agent_mode.py` | 2 | LEGACY | 🟢 | إضافة المصادر المتعددة (روابط + ملفات) لوضع الأيجنتس |
| `01.04_notegpt_agent_mode.py` | 3 | LEGACY | 🟢 | Auto Drop-Folder + تدوير IP نقي |
| `01.05_notegpt_agent_mode.py` | 4 | LEGACY | 🟢 | مطابقة كاملة مع HAR الأخير: Native Files Payload + History Sync |
| `01.06_notegpt_agent_mode.py` | 5 | LEGACY | 🟢 | Smart Git Rebase + Live Browser Sidebar Sync |

*🟢 موثوق (verified أو مؤلفه Builder+) · 🟡 لم يُختبر · 🔴 فشل موثق*
