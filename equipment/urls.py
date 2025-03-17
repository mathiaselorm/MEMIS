from django.urls import path
from . import views




urlpatterns = [
    # Supplier endpoints
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),

    # Equipment endpoints
    path('equipment/', views.EquipmentList.as_view(), name='equipment-list'),
    path('equipment/<int:pk>/', views.EquipmentDetail.as_view(), name='equipment-detail'),
    
    # Total equipment count
    path('equipment/total/', views.TotalEquipmentView.as_view(), name='total-equipment'),
    
    # Equipment status breakdown (functional, under maintenance, etc.)
    path('equipment-status/summary/', views.EquipmentStatusSummaryView.as_view(), name='equipment-status-summary'),
        
    # Equipment type breakdown (diagnostic, therapeutic, etc.)
    path('equipment-type/summary/', views.EquipmentTypeSummaryView.as_view(), name='equipment-type-summary'),

    
    # Maintenance activity overview (daily counts over a chosen period)
    path('maintenance-reports/overview/', views.MaintenanceActivityOverviewView.as_view(), name='maintenance-reports-overview'),
    
    # Report
    path('maintenance-reports/', views.MaintenanceActivitiesListCreateView.as_view(), name='maintenance-reports'),
    path('maintenance-reports/<int:pk>/', views.MaintenanceActivitiesDetailView.as_view(), name='maintenance-report-detail'),
    
    # # Equipment Maintenance Reports
    path('equipment/<int:equipment_id>/maintenance-reports/', views.MaintenanceActivitiesByEquipmentView.as_view(), name='equipment-activities'),
    path('equipment/<int:equipment_id>/maintenance-reports/<int:activity_id>/', views.MaintenanceActivitiesDetailByEquipmentView.as_view(), name='equipment-activity-detail-by-equipment'),
    path('equipment/<int:equipment_id>/maintenance-reports/yearly-overview/', views.EquipmentMaintenanceActivityYearlyOverviewView.as_view(), name='equipment-activity-yearly-overview'),
    
    # Upcoming maintenance schedules for the current month
    path('maintenance/upcoming-schedules/', views.UpcomingMaintenanceScheduleView.as_view(), name='upcoming-maintenance-schedules'),
    
    # Maintenance schedule endpoints
    path('maintenance-schedules/', views.MaintenanceScheduleListCreateView.as_view(), name='maintenance-schedule-list-create'),
    path('maintenance-schedules/<int:pk>/', views.MaintenanceScheduleDetailView.as_view(), name='maintenance-schedule-detail'),
    path('maintenance-schedules/<int:pk>/deactivate/', views.deactivate_schedule, name='schedule-deactivate'),
    
]

