from django.db import models
import json


class SurveyDataset(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    total_records = models.IntegerField(default=0)
    processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name


class SurveyRecord(models.Model):
    STATUS_CHOICES = [
        ('clean', 'بيانات سليمة'),
        ('review', 'تحتاج مراجعة'),
        ('error', 'خطأ منطقي'),
        ('pending', 'قيد المعالجة'),
    ]

    dataset = models.ForeignKey(SurveyDataset, on_delete=models.CASCADE, related_name='records')
    record_number = models.IntegerField()
    data = models.JSONField()
    confidence_score = models.FloatField(null=True, blank=True)
    issues = models.JSONField(default=list, blank=True)
    explanation = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['record_number']

    def __str__(self):
        return f"سجل #{self.record_number} - {self.get_status_display()}"

    @property
    def issues_list(self):
        if isinstance(self.issues, list):
            return self.issues
        return []

    @property
    def status_color(self):
        colors = {
            'clean': '#10B981',
            'review': '#F59E0B',
            'error': '#EF4444',
            'pending': '#6B7280',
        }
        return colors.get(self.status, '#6B7280')

    @property
    def status_label(self):
        labels = {
            'clean': 'بيانات سليمة',
            'review': 'تحتاج مراجعة',
            'error': 'خطأ منطقي',
            'pending': 'قيد المعالجة',
        }
        return labels.get(self.status, 'غير معروف')
