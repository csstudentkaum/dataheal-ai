import json
import os
import random
from django.conf import settings

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def get_validation_prompt(record_data: dict) -> str:
    """Build a few-shot prompt for semantic validation."""
    fields_text = "\n".join([f"{k}: {v}" for k, v in record_data.items()])

    prompt = """أنت نظام ذكاء اصطناعي متخصص في تحليل بيانات الاستبيانات.

مهمتك اكتشاف التناقضات المنطقية والدلالية بين الحقول المختلفة في سجل الاستبيان.

يجب أن تتحقق من:
1. تناسب العمر مع سنوات الخبرة (لا يمكن أن تكون سنوات الخبرة أكبر من العمر - 18)
2. تناسب المسمى الوظيفي مع المؤهل العلمي
3. تناسب الدخل مع المسمى الوظيفي والخبرة
4. منطقية الحالة الاجتماعية مع العمر
5. أي تناقضات أخرى بين الحقول

مثال 1:
Age: 21
Years Experience: 10
Job Title: Senior Manager
Education: High School

النتيجة:
{
  "confidence_score": 0.3,
  "issues": [
    "سنوات الخبرة (10) غير منطقية مقارنة بالعمر (21)، حيث أن الحد الأقصى المعقول هو 3 سنوات",
    "المسمى الوظيفي (Senior Manager) لا يتوافق مع المؤهل العلمي (High School)"
  ],
  "explanation": "يوجد تناقض واضح بين العمر وسنوات الخبرة، وكذلك بين المسمى الوظيفي والمؤهل العلمي."
}

مثال 2:
Age: 45
Education: PhD
Job Title: Professor
Years Experience: 20

النتيجة:
{
  "confidence_score": 0.95,
  "issues": [],
  "explanation": "لا توجد تناقضات منطقية. البيانات متسقة ومنطقية."
}

الآن حلل السجل التالي وأعد النتيجة بصيغة JSON فقط:

""" + fields_text + """

أعد الإجابة بصيغة JSON فقط بالشكل التالي:
{
  "confidence_score": <رقم بين 0 و 1>,
  "issues": [<قائمة المشاكل بالعربية>],
  "explanation": "<شرح مختصر بالعربية>"
}"""

    return prompt


def validate_with_openai(record_data: dict) -> dict:
    """Validate a record using OpenAI API."""
    api_key = settings.OPENAI_API_KEY

    if not api_key or not HAS_OPENAI:
        return validate_with_rules(record_data)

    try:
        client = OpenAI(api_key=api_key)
        prompt = get_validation_prompt(record_data)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "أنت خبير في تحليل جودة البيانات والكشف عن التناقضات المنطقية. أجب بصيغة JSON فقط."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800,
        )

        result_text = response.choices[0].message.content.strip()
        # Extract JSON from response
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        return {
            "confidence_score": float(result.get("confidence_score", 0.5)),
            "issues": result.get("issues", []),
            "explanation": result.get("explanation", ""),
        }
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return validate_with_rules(record_data)


def validate_with_rules(record_data: dict) -> dict:
    """Rule-based fallback validator when no API key is available."""
    issues = []
    explanation_parts = []

    # Normalize keys to lowercase
    data = {k.lower().replace(' ', '_'): v for k, v in record_data.items()}

    # Convert numeric fields
    age = _to_number(data.get('age'))
    years_exp = _to_number(data.get('years_experience') or data.get('experience'))
    income = _to_number(data.get('income') or data.get('salary'))
    education = str(data.get('education', '')).lower().strip()
    job_title = str(data.get('job_title', '') or data.get('job', '')).lower().strip()
    gender = str(data.get('gender', '')).lower().strip()
    marital = str(data.get('marital_status', '')).lower().strip()

    # Rule 1: Age vs Experience
    if age is not None and years_exp is not None:
        max_reasonable_exp = max(0, age - 16)
        if years_exp > max_reasonable_exp:
            issues.append(
                f"سنوات الخبرة ({years_exp}) غير منطقية مقارنة بالعمر ({age}). الحد الأقصى المعقول هو {max_reasonable_exp} سنة"
            )
            explanation_parts.append("العمر المذكور لا يدعم عدد سنوات الخبرة المذكورة")

    # Rule 2: Job Title vs Education
    senior_titles = ['senior', 'manager', 'director', 'professor', 'surgeon', 'doctor', 'chief', 'head', 'lead', 'principal', 'vp', 'ceo', 'cto', 'cfo']
    low_education = ['high school', 'secondary', 'ثانوي', 'ثانوية', 'middle school', 'إعدادي', 'primary', 'ابتدائي']

    if job_title and education:
        is_senior = any(t in job_title for t in senior_titles)
        is_low_edu = any(e in education for e in low_education)
        if is_senior and is_low_edu:
            issues.append(
                f"المسمى الوظيفي ({data.get('job_title', '')}) لا يتوافق مع المؤهل العلمي ({data.get('education', '')})"
            )
            explanation_parts.append("المؤهل العلمي لا يتناسب مع المسمى الوظيفي")

    # Rule 4: Age vs Marital Status
    if age is not None and age < 14 and marital in ['married', 'متزوج', 'متزوجة', 'divorced', 'مطلق', 'مطلقة', 'widowed', 'أرمل', 'أرملة']:
        issues.append(f"الحالة الاجتماعية ({data.get('marital_status', '')}) غير منطقية مع العمر ({age})")
        explanation_parts.append("العمر صغير جدًا للحالة الاجتماعية المذكورة")

    # Rule 5: Age vs Job title (too young for senior roles)
    if age is not None and age < 25 and job_title:
        is_senior = any(t in job_title for t in senior_titles)
        if is_senior:
            issues.append(f"العمر ({age}) صغير جدًا للمسمى الوظيفي ({data.get('job_title', '')})")
            explanation_parts.append("العمر لا يتناسب مع المسمى الوظيفي")

    # Rule 6: Income anomalies
    if income is not None and years_exp is not None:
        if income > 50000 and years_exp < 2:
            issues.append(f"الدخل ({income}) مرتفع جدًا مقارنة بسنوات الخبرة ({years_exp})")
            explanation_parts.append("الدخل لا يتناسب مع الخبرة")

    # Calculate confidence score
    if not issues:
        confidence = round(random.uniform(0.88, 0.99), 2)
        explanation = "لا توجد تناقضات منطقية. البيانات متسقة ومنطقية."
    else:
        # More issues = lower confidence
        penalty = len(issues) * 0.2
        confidence = round(max(0.1, 0.85 - penalty + random.uniform(-0.05, 0.05)), 2)
        explanation = ". ".join(explanation_parts) + "."

    return {
        "confidence_score": confidence,
        "issues": issues,
        "explanation": explanation,
    }


def determine_status(confidence_score: float, issues: list) -> str:
    """Determine record status based on confidence and issues."""
    if not issues or confidence_score >= 0.85:
        return 'clean'
    elif confidence_score >= 0.5:
        return 'review'
    else:
        return 'error'


def _to_number(val):
    """Safely convert a value to a number."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def generate_sample_dataset(num_records=20):
    """Generate a sample dataset with intentional logical errors for demo."""
    import csv
    import io

    records = []
    # Clean records
    clean_data = [
        {"age": 35, "gender": "Male", "education": "Master", "job_title": "Software Engineer", "years_experience": 12, "marital_status": "Married", "income": 25000},
        {"age": 45, "gender": "Female", "education": "PhD", "job_title": "Professor", "years_experience": 20, "marital_status": "Married", "income": 45000},
        {"age": 28, "gender": "Male", "education": "Bachelor", "job_title": "Accountant", "years_experience": 5, "marital_status": "Single", "income": 12000},
        {"age": 50, "gender": "Female", "education": "Master", "job_title": "Director", "years_experience": 25, "marital_status": "Married", "income": 55000},
        {"age": 30, "gender": "Male", "education": "Bachelor", "job_title": "Teacher", "years_experience": 7, "marital_status": "Married", "income": 10000},
        {"age": 40, "gender": "Female", "education": "PhD", "job_title": "Senior Researcher", "years_experience": 15, "marital_status": "Divorced", "income": 35000},
        {"age": 26, "gender": "Male", "education": "Bachelor", "job_title": "Graphic Designer", "years_experience": 3, "marital_status": "Single", "income": 8000},
        {"age": 55, "gender": "Female", "education": "Master", "job_title": "Head of Department", "years_experience": 30, "marital_status": "Widowed", "income": 60000},
        {"age": 33, "gender": "Male", "education": "Bachelor", "job_title": "Marketing Manager", "years_experience": 10, "marital_status": "Married", "income": 20000},
        {"age": 29, "gender": "Female", "education": "Master", "job_title": "Data Analyst", "years_experience": 4, "marital_status": "Single", "income": 15000},
    ]

    # Records with logical errors
    error_data = [
        {"age": 22, "gender": "Male", "education": "High School", "job_title": "Senior Surgeon", "years_experience": 15, "marital_status": "Married", "income": 80000},
        {"age": 19, "gender": "Male", "education": "Secondary", "job_title": "Senior Manager", "years_experience": 12, "marital_status": "Single", "income": 50000},
        {"age": 25, "gender": "Male", "education": "Bachelor", "job_title": "Engineer", "years_experience": 20, "marital_status": "Married", "income": 30000},
        {"age": 21, "gender": "Male", "education": "High School", "job_title": "Chief Doctor", "years_experience": 8, "marital_status": "Single", "income": 70000},
        {"age": 30, "gender": "Male", "education": "Bachelor", "job_title": "Nurse", "years_experience": 7, "marital_status": "Married", "income": 12000},
        {"age": 10, "gender": "Female", "education": "PhD", "job_title": "Professor", "years_experience": 25, "marital_status": "Married", "income": 90000},
        {"age": 23, "gender": "Female", "education": "High School", "job_title": "Senior Director", "years_experience": 1, "marital_status": "Single", "income": 95000},
        {"age": 18, "gender": "Male", "education": "Primary", "job_title": "CEO", "years_experience": 10, "marital_status": "Divorced", "income": 100000},
        {"age": 20, "gender": "Female", "education": "Secondary", "job_title": "Lead Architect", "years_experience": 14, "marital_status": "Single", "income": 45000},
        {"age": 24, "gender": "Male", "education": "High School", "job_title": "Senior VP", "years_experience": 18, "marital_status": "Married", "income": 120000},
    ]

    records = clean_data + error_data
    random.shuffle(records)

    # Build CSV
    output = io.StringIO()
    fieldnames = ["age", "gender", "education", "job_title", "years_experience", "marital_status", "income"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        row = {f: r.get(f, "") for f in fieldnames}
        writer.writerow(row)

    return output.getvalue()
