from django.urls import path
from . import views





urlpatterns = [
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('notifications/mark_all_read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
]