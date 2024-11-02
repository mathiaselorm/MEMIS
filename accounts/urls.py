from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenVerifyView,
    TokenRefreshView
)

urlpatterns = [
    # Authentication endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', views.logout_view, name='logout'),
    path('login/token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/token-verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('password-reset/', views.CustomPasswordResetRequestView.as_view(), name='password_reset'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),

    # User management endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/total/', views.total_users_view, name='total-users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:id>/assign-role/', views.RoleAssignmentView.as_view(), name='assign-role'),

    # Audit logs endpoint
    path('audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),
]
