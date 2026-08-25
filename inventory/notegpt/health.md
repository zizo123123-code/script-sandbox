# 🩺 NoteGPT — Health Checks & Readiness Probes (`health.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED` بناءً على فحص ملفات الـ HAR وكود `01.05`.

---

## 1. الـ Endpoints الحقيقية لفحص صحة الحساب والخدمة

| الغرض | الـ Endpoint الفعلي | Method | الدليل في الـ HAR | معيار النجاح (PASS) |
|---|---|---|---|---|
| **فحص الاتصال ومعلومات المستخدم** | **`/api/v1/userinfo`** | `GET` | HAR ×10 | `code == 100000` |
| **فحص حصة الخطة (Plan Quota)** | **`/api/v2/plan-quota`** | `GET` | HAR ×212 | `code == 100000` |
| **فحص استهلاك الحصة (Quota Usage)** | **`/api/v2/user/quota-usage`** | `GET` | HAR ×212 | `code == 100000` |
| **فحص حصة المستخدم العامة** | **`/api/v2/user/quota`** | `GET` | HAR ×11 | `code == 100000` |
| **فحص صلاحيات الدفع** | **`/api/v2/payments/check-user-permissions`** | `GET` | HAR ×6 | `code == 100000` |

---

## 2. معايير الفحص والجاهزية
- **كود النجاح الرسمي:** هو `100000` دائماً في حقل الـ JSON.
- **مؤشر استقرار الخدمة:** يتم التحقق الدوري من استجابة `GET /api/v2/plan-quota` للتأكد من أن الكوكيز نشطة والحساب غير مقيد بحظر أو نفاد رصيد.
