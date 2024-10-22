from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenVerifyView,
)

urlpatterns = [
                        #ADMIN URLS
    # Registration endpoint for new users. This view handles user creation 
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    # Endpoint for changing the user type of a user.
    path('assign-role/', views.RoleAssignmentView.as_view(), name='assign-role'),
    
    # endpoint for Admin login
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token-refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('login/token-verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', views.logout_view, name='logout'),

    # Password endpoints
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    path('password/reset-request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/<uidb64>/<token>/', views.PasswordResetView.as_view(), name='password_reset_confirm'),

    
    
    # Endpoint for listing all users in the system.
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/total/', views.total_users_view, name='total-users'),     
    
    path('audit-logs/', views.AuditLogView.as_view(), name='audit-logs'),
]
