from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/', views.upload_view, name='upload'),
    path('validate/<int:dataset_id>/', views.validate_dataset, name='validate_dataset'),
    path('dashboard/<int:dataset_id>/', views.dashboard_view, name='dashboard'),
    path('datasets/', views.all_datasets, name='all_datasets'),
    path('validate-record', views.validate_record_api, name='validate_record_api'),
    path('download-report/<int:dataset_id>/', views.download_report, name='download_report'),
    path('generate-sample/', views.generate_sample, name='generate_sample'),
    path('api/record/<int:record_id>/', views.record_detail_api, name='record_detail_api'),
]
