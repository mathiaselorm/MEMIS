from django.urls import path
from . import views




urlpatterns = [
    # Department endpoints
    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('departments/total/', views.TotalDepartmentsView.as_view(), name='total-departments'),
    path('departments/<str:identifier>/', views.DepartmentDetail.as_view(), name='department-detail'),

    # Asset endpoints
    path('assets/', views.AssetList.as_view(), name='asset-list'),
    path('assets/total/', views.TotalAssetsView.as_view(), name='total-assets'),
    path('assets/under-maintenance/', views.TotalAssetsUnderMaintenanceView.as_view(), name='assets-under-maintenance'),
    path('assets/<int:pk>/', views.AssetDetail.as_view(), name='asset-detail'),

    # Tracking endpoints
    path('assets/department/<str:identifier>/', views.TrackingByDepartmentView.as_view(), name='assets-by-department'),
    path('assets/status/', views.TrackingByOperationalStatusView.as_view(), name='assets-by-operational-status'),

    # Audit log endpoint
    path('assets/audit-logs/', views.AuditLogView.as_view(), name='audit-log'),
]