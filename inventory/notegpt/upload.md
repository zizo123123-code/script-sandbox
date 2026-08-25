# 📤 NoteGPT — Upload & Asset Processing (`upload.md`)

> **المزود:** NoteGPT (`notegpt.io`)  
> **حالة التوثيق:** `CONFIRMED` بناءً على ملفات الـ HAR (`200 OK`) وكود `01.05:174-182`.

---

## 1. مسار الرفع الحقيقي (2-Step Alibaba OSS Upload Flow)

لا تعتمد منصة NoteGPT على `POST /upload` مباشر، بل تستخدم مسار التوقيع السحابي المعتمد:

### 🔹 الخطوة 1: طلب توقيع الرابط (Sign URL Request)
```http
POST https://notegpt.io/api/v1/upload/sign-url
Content-Type: application/json

{
  "t": 1787635752,
  "app_id": "notegpt_8c92b6",
  "filename": "image.png",
  "file_size": 110637,
  "headers": {"Content-Type": "image/png"},
  "biz": "ai-chat",
  "sign": "<HMAC_SHA256_SIGNATURE>"
}
```
**استجابة الخادم:**
```json
{
  "code": 100000,
  "message": "success",
  "data": {
    "object_key": "product/upload/notegpt/ai-chat/2026/08/25/<hash>.png",
    "upload_url": "https://nc-product-us-oss.oss-us-west-1.aliyuncs.com/...?OSSAccessKeyId=...&Expires=1787636354&Signature=..."
  }
}
```

### 🔹 الخطوة 2: الرفع المباشر إلى خادم التخزين السحابي
```http
PUT https://nc-product-us-oss.oss-us-west-1.aliyuncs.com/product/upload/notegpt/ai-chat/...
Content-Type: image/png

<BINARY_IMAGE_DATA>
```

---

## 2. مواصفات الروابط والمرفقات

| البند | القيمة الحقيقية المؤكدة | الدليل / المصدر |
|---|---|---|
| **المضيف السحابي للرفع** | `nc-product-us-oss.oss-us-west-1.aliyuncs.com` | HAR `200 OK` |
| **صلاحية رابط الرفع** | **مؤقتة (~10 دقائق)** (`Expires=1787636354`) | استجابة الـ sign-url |
| **الحد الأقصى للحجم** | `UNKNOWN` (لا يوجد قيد برمجياً في الكود) | `01.05` |
| **الصيغ المدعومة** | `UNKNOWN` (الكود يقبل أي بايتات) | `01.05` |
| **الروابط البديلة في الكود** | استخدام `tmpfiles.org` كبديل خارجي مؤقت | `01.05:174` |
| **رابط الـ CDN الافتراضي** | `cdn.ng-resource.com` كـ fallback افتراضي | `01.05:182` |
