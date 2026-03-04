# DataHeal AI — تصحيح البيانات الدلالي الذكي

**DataHeal AI** هو نموذج أولي لنظام يعتمد على الذكاء الاصطناعي لاكتشاف التناقضات المنطقية والدلالية في بيانات الاستبيانات قبل استخدامها في التحليل.

🔗 **عرض المشروع:**
https://dataheal-ai.onrender.com

---

## المميزات

* رفع بيانات الاستبيان بصيغة **CSV** أو **JSON**
* تحليل السجلات لاكتشاف التناقضات المنطقية
* لوحة تحكم لعرض النتائج ودرجات الثقة
* تحميل نتائج التحليل بصيغة **CSV**
* واجهة عربية تدعم **RTL**

---

## كيف يعمل النظام

1. **رفع البيانات**
   يقوم المستخدم برفع ملف الاستبيان بصيغة CSV أو JSON.

2. **تحليل السجلات**
   يتم تحليل كل سجل لاكتشاف التناقضات المنطقية بين الحقول.

3. **عرض النتائج**
   تظهر النتائج في لوحة التحكم مع درجة الثقة والتفسيرات.

---

## الأدوات المستخدمة

* **Python**
* **Django**
* **HTML / CSS / Bootstrap**
* **JavaScript**
* **Large Language Models (LLM)**
* **SQLite**
* **Render** (Deployment)

---

## تشغيل المشروع محليًا

### إنشاء البيئة وتثبيت المتطلبات

```bash
cd dataheal_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### إعداد قاعدة البيانات

```bash
python manage.py migrate
```

### تشغيل الخادم

```bash
python manage.py runserver
```

ثم افتح المتصفح:

http://127.0.0.1:8000

---

## هيكل المشروع

```
dataheal_ai/
├── manage.py
├── requirements.txt
├── dataheal_ai/
├── validator/
│   ├── models.py
│   ├── views.py
│   ├── ai_validator.py
│   ├── urls.py
│   └── templates/
├── static/
└── media/uploads/
```

---

نموذج أولي يوضح كيف يمكن استخدام الذكاء الاصطناعي لتحسين جودة بيانات الاستبيانات واكتشاف الأخطاء مبكرًا.
