import csv
import json
import io
import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.conf import settings

from .models import SurveyDataset, SurveyRecord
from .ai_validator import validate_with_openai, determine_status, generate_sample_dataset

logger = logging.getLogger(__name__)


def home(request):
    """Landing page."""
    datasets = SurveyDataset.objects.all()[:5]
    return render(request, 'validator/home.html', {'datasets': datasets})


def upload_view(request):
    """Upload survey data page."""
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, 'الرجاء اختيار ملف للرفع')
            return render(request, 'validator/upload.html')

        filename = uploaded_file.name.lower()
        if not (filename.endswith('.csv') or filename.endswith('.json')):
            messages.error(request, 'صيغة الملف غير مدعومة. الرجاء رفع ملف CSV أو JSON')
            return render(request, 'validator/upload.html')

        try:
            # Ensure media/uploads directory exists
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            # Read content BEFORE saving (in case seek fails after save)
            content = uploaded_file.read().decode('utf-8')

            # Reset for Django to save the file
            uploaded_file.seek(0)

            # Create dataset
            dataset = SurveyDataset.objects.create(
                name=uploaded_file.name,
                file=uploaded_file,
            )

            # Parse file
            if filename.endswith('.csv'):
                records = _parse_csv(content)
            else:
                records = _parse_json(content)

            dataset.total_records = len(records)
            dataset.save()

            # Create survey records
            for i, record_data in enumerate(records, 1):
                SurveyRecord.objects.create(
                    dataset=dataset,
                    record_number=i,
                    data=record_data,
                )

            messages.success(request, f'تم رفع الملف بنجاح! تم العثور على {len(records)} سجل.')
            return redirect('validate_dataset', dataset_id=dataset.id)

        except Exception as e:
            logger.error(f'Upload error: {e}', exc_info=True)
            if 'dataset' in locals():
                dataset.delete()
            messages.error(request, f'حدث خطأ أثناء معالجة الملف: {str(e)}')
            return render(request, 'validator/upload.html')

    return render(request, 'validator/upload.html')


def validate_dataset(request, dataset_id):
    """Validate all records in a dataset using AI."""
    dataset = get_object_or_404(SurveyDataset, id=dataset_id)
    records = dataset.records.all()

    # Process unvalidated records
    for record in records.filter(status='pending'):
        result = validate_with_openai(record.data)
        record.confidence_score = result['confidence_score']
        record.issues = result['issues']
        record.explanation = result['explanation']
        record.status = determine_status(result['confidence_score'], result['issues'])
        record.validated_at = timezone.now()
        record.save()

    dataset.processed = True
    dataset.save()

    return redirect('dashboard', dataset_id=dataset.id)


def dashboard_view(request, dataset_id):
    """Dashboard displaying validation results."""
    dataset = get_object_or_404(SurveyDataset, id=dataset_id)
    records = dataset.records.all()

    # Summary stats
    total = records.count()
    clean_count = records.filter(status='clean').count()
    error_count = records.filter(status='error').count()
    review_count = records.filter(status='review').count()

    scores = [r.confidence_score for r in records if r.confidence_score is not None]
    avg_confidence = round(sum(scores) / len(scores) * 100, 1) if scores else 0

    context = {
        'dataset': dataset,
        'records': records,
        'total': total,
        'clean_count': clean_count,
        'error_count': error_count,
        'review_count': review_count,
        'avg_confidence': avg_confidence,
    }
    return render(request, 'validator/dashboard.html', context)


def all_datasets(request):
    """List all datasets."""
    datasets = SurveyDataset.objects.all()
    return render(request, 'validator/datasets.html', {'datasets': datasets})


@csrf_exempt
@require_POST
def validate_record_api(request):
    """API endpoint for real-time single record validation."""
    try:
        data = json.loads(request.body)
        result = validate_with_openai(data)
        result['status'] = determine_status(result['confidence_score'], result['issues'])
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'صيغة JSON غير صالحة'}, status=400, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500, json_dumps_params={'ensure_ascii': False})


def download_report(request, dataset_id):
    """Download validation report as CSV."""
    dataset = get_object_or_404(SurveyDataset, id=dataset_id)
    records = dataset.records.all()

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="dataheal_report_{dataset_id}.csv"'
    response.write('\ufeff')  # BOM for Arabic support in Excel

    writer = csv.writer(response)
    writer.writerow(['رقم السجل', 'درجة الثقة', 'الحالة', 'المشكلات المكتشفة', 'الشرح', 'البيانات الأصلية'])

    for record in records:
        issues_text = ' | '.join(record.issues) if record.issues else 'لا توجد مشاكل'
        status_label = record.status_label
        data_text = json.dumps(record.data, ensure_ascii=False)
        writer.writerow([
            record.record_number,
            record.confidence_score,
            status_label,
            issues_text,
            record.explanation,
            data_text,
        ])

    return response


def generate_sample(request):
    """Generate and download a sample dataset with errors."""
    csv_content = generate_sample_dataset()
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="sample_survey_data.csv"'
    return response


def record_detail_api(request, record_id):
    """Get details for a specific record (AJAX)."""
    record = get_object_or_404(SurveyRecord, id=record_id)
    return JsonResponse({
        'record_number': record.record_number,
        'data': record.data,
        'confidence_score': record.confidence_score,
        'issues': record.issues,
        'explanation': record.explanation,
        'status': record.status,
        'status_label': record.status_label,
        'status_color': record.status_color,
    }, json_dumps_params={'ensure_ascii': False})


def _parse_csv(content):
    """Parse CSV content into list of dicts."""
    reader = csv.DictReader(io.StringIO(content))
    records = []
    for row in reader:
        cleaned = {k.strip(): v.strip() for k, v in row.items() if k and v and v.strip()}
        if cleaned:
            records.append(cleaned)
    return records


def _parse_json(content):
    """Parse JSON content into list of dicts."""
    data = json.loads(content)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        if 'records' in data:
            return data['records']
        elif 'data' in data:
            return data['data']
        return [data]
    return []
