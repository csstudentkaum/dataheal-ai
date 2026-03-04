# DataHeal AI — تصحيح البيانات الدلالي الذكي

نظام ذكاء اصطناعي لاكتشاف التناقضات المنطقية والدلالية في بيانات الاستبيانات.

🔗 **[عرض المشروع مباشرة](https://dataheal-ai.onrender.com)**

## المميزات

- **رفع بيانات الاستبيان**: دعم ملفات CSV و JSON
- **تحليل ذكي**: كشف التناقضات باستخدام LLM أو قواعد ذكية
- **لوحة تحكم تفاعلية**: عرض النتائج مع درجات الثقة
- **واجهة برمجية (API)**: تحقق لحظي من السجلات
- **تقارير**: تحميل نتائج التحليل بصيغة CSV
- **واجهة عربية RTL**: دعم كامل للغة العربية

## التشغيل المحلي

### 1. إنشاء بيئة افتراضية

```bash
cd dataheal_ai
python3 -m venv venv
source venv/bin/activate
```

### 2. تثبيت المتطلبات

```bash
pip install -r requirements.txt
```

### 3. إعداد قاعدة البيانات

```bash
python manage.py migrate
```

### 4. (اختياري) إضافة مفتاح OpenAI API

افتح ملف `.env` وأضف مفتاح API:

```
OPENAI_API_KEY=sk-your-key-here
```

> **ملاحظة**: إذا لم يتم إضافة مفتاح، سيستخدم النظام محرك تحقق مبني على قواعد ذكية.

### 5. تشغيل الخادم

```bash
python manage.py runserver
```

### 6. فتح المتصفح

افتح: [http://127.0.0.1:8000](http://127.0.0.1:8000)

## استخدام API

```bash
curl -X POST http://127.0.0.1:8000/validate-record \
  -H "Content-Type: application/json" \
  -d '{"age": 22, "job_title": "Senior Engineer", "years_experience": 12}'
```

## هيكل المشروع

```
dataheal_ai/
├── manage.py
├── requirements.txt
├── .env
├── dataheal_ai/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── validator/
│   ├── models.py
│   ├── views.py
│   ├── ai_validator.py
│   ├── urls.py
│   ├── admin.py
│   ├── apps.py
│   └── templates/validator/
│       ├── base.html
│       ├── home.html
│       ├── upload.html
│       ├── dashboard.html
│       └── datasets.html
├── static/
└── media/uploads/
```
