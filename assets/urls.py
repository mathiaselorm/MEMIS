from django.urls import path
from . import views




urlpatterns = [
    # Asset URLs
    path('assets/', views.AssetList.as_view(), name='asset-list'),
    path('assets/<uuid:pk>/', views.AssetDetail.as_view(), name='asset-detail'),
    path('assets/total/', views.TotalAssetsView.as_view(), name='total-assets'),
    path('assets/under-maintenance/', views.TotalAssetsUnderMaintenanceView.as_view(), name='assets-maintenance-count'),


    # Department URLs
    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('departments/<str:identifier>/', views.DepartmentDetail.as_view(), name='department-detail'),
    path('total_departments/', views.TotalDepartmentsView.as_view(), name='total-departments'),
    path('departments/<str:identifier>/assets/', views.TrackingByDepartmentView.as_view(), name='department-assets'),
    path('assets/status/tracking/', views.TrackingByStatusView.as_view(), name='assets-by-status'),
    
    path('auditlogs/', views.AuditLogView.as_view(), name='audit-logs'),
    path('actionlogs/', views.ActionLogView.as_view(), name='action-logs'),
]