from django.urls import path
from django_rest_passwordreset.views import (
    ResetPasswordConfirm, 
    ResetPasswordValidateToken,
    # ResetPasswordRequestToken
)

from . import views

urlpatterns = [
    # Authentication endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('logout/', views.logout_view, name='logout'),
    path('login/token-refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('password-reset/request/', views.CustomPasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset/confirm/', ResetPasswordConfirm.as_view(), name='password_reset_confirm'),
    path('password-reset/validate/', ResetPasswordValidateToken.as_view(), name='password_reset_validate'),
    path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),

    # User management endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/total/', views.total_users_view, name='total-users'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:id>/assign-role/', views.RoleAssignmentView.as_view(), name='assign-role'),
]
