from django.urls import path
from . import views




urlpatterns = [
    # Department endpoints
    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('departments/total/', views.TotalDepartmentsView.as_view(), name='total-departments'),
    path('departments/<str:identifier>/', views.DepartmentDetail.as_view(), name='department-detail'),
    
    # Supplier endpoints
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),

    # Equipment endpoints
    path('equipment/', views.EquipmentList.as_view(), name='equipment-list'),
    path('equipment/total/', views.TotalEquipmentView.as_view(), name='total-equipment'),
    path('equipment/under-maintenance/', views.TotalEquipmentUnderMaintenanceView.as_view(), name='equipment-under-maintenance'),
    path('equipment/<int:pk>/', views.EquipmentDetail.as_view(), name='equipment-detail'),

    # Equipment Maintenance Activities endpoints
    path('equipment/<int:equipment_id>/maintenance-activities/', views.MaintenanceActivitiesByEquipmentView.as_view(), name='equipment-activities-by-equipment'),
    path('equipment/<int:equipment_id>/maintenance-activities/<int:activity_id>/', views.MaintenanceActivitiesDetailByEquipmentView.as_view(), name='equipment-activity-detail-by-equipment'),
    path('maintenace-activities/', views.MaintenanceActivitiesListCreateView.as_view(), name='equipment-maintenance-activity-list-create'),
    path('maintenace-activities/<int:pk>/', views.MaintenanceActivitiesDetailView.as_view(), name='equipment-maintenance-activity-detail'),

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