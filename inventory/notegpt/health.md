# 🩺 NoteGPT — Health Checks & Readiness Probes (`health.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED`

---

## 1. مؤشرات الجاهزية والصحة (Liveness & Readiness Probes)

| نوع الفحص | الـ Endpoint / الإشارة | معيار النجاح (PASS) | معيار الفشل (FAIL) |
|---|---|---|---|
| **فحص الاتصال (Ping)** | `GET https://notegpt.io/` | `200 OK` | `5xx` أو حظر Cloudflare |
| **فحص صلاحية التوكن** | `GET /api/v2/user/info` | `{"code": 0, "data": {...}}` | `401 Unauthorized` |
| **فحص رصيد الكريديت** | `GET /api/v2/plan/quota` | `remaining_credit > 0` | `remaining_credit == 0` |
| **فحص استجابة الساندبوكس** | إرسال أمر تجريبي سريع (`echo 1`) | استلام `tool_result` في 3 ثوانٍ | مهلة زمنية تتجاوز 15 ثانية |

---

## 2. استنتاج حالة المزود بدون Endpoint مخصص
- مراقبة معدل النجاح (Success Rate): إذا انخفض عن 80% في آخر 5 طلبات، يتم وسم المزود بحالة `DEGRADED`.
- عند تكرار خطأ 504 لأكثر من 3 مرات متتالية، يتم تحويل الطلبات إلى مزود بديل مؤقتاً.
