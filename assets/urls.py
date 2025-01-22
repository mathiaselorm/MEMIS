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
    
    path('assets/<int:pk>/restore/', views.restore_asset, name='restore-asset'),
    
    #Assets Activities endpoints
    path('assets/<int:asset_id>/activities/', views.AssetActivitiesByAssetView.as_view(), name='asset-activities-by-asset'),
    path('assets/<int:asset_id>/activities/<int:activity_id>/', views.AssetActivityDetailByAssetView.as_view(), name='asset-activity-detail-by-asset'),
    
    path('asset-activities/', views.AssetActivityListCreateView.as_view(), name='asset-activity-list-create'),
    path('asset-activities/<int:pk>/', views.AssetActivityDetailView.as_view(), name='asset-activity-detail'),
    
    # Audit log endpoint
    path('assets/audit-logs/', views.AuditLogView.as_view(), name='audit-log'),
    
    # Maintenance schedule endpoints
    path('maintenance-schedules/', views.MaintenanceScheduleListCreateView.as_view(), name='maintenance-schedule-list-create'),
    path('maintenance-schedules/<int:pk>/', views.MaintenanceScheduleDetailView.as_view(), name='maintenance-schedule-detail'),
    path('maintenance-schedules/<int:pk>/deactivate/', views.deactivate_schedule, name='schedule-deactivate'),
    
]






    # Tracking endpoints
    # path('assets/department/<str:identifier>/', views.TrackingByDepartmentView.as_view(), name='assets-by-department'),
    # path('assets/status/', views.TrackingByOperationalStatusView.as_view(), name='assets-by-operational-status'),
    # path('assets/softdeleted/', views.SoftDeletedAssetsView.as_view(), name='soft-deleted-assets'),
    # path('assets/<int:pk>/delete/', views.permanent_delete_asset, name='delete-softdeleted-assets'),