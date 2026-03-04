from django.contrib import admin
from .models import SurveyDataset, SurveyRecord

@admin.register(SurveyDataset)
class SurveyDatasetAdmin(admin.ModelAdmin):
    list_display = ['name', 'total_records', 'processed', 'uploaded_at']

@admin.register(SurveyRecord)
class SurveyRecordAdmin(admin.ModelAdmin):
    list_display = ['record_number', 'dataset', 'confidence_score', 'status']
    list_filter = ['status']
