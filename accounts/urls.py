from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
                        #ADMIN URLS
    # Registration endpoint for new users. This view handles user creation 
    path('admin/register/', views.UserRegistrationView.as_view(), name='register'),
    
       # Endpoint for changing the user type of a user.
    path('admin/user/<int:pk>/update-role/', views.UpdateUserRoleView.as_view(), name='update_user_role'),
    
    # endpoint for Admin login
    path('admin/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('admin/login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('admin/login/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Endpoint for viewing user details.
    path('admin/user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Endpoint for admin to change password
    path('admin/password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    
    # Endpoint for requesting a password reset email.
    path('admin/password/reset-request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    
    # Endpoint for listing all users in the system.
    path('admin/users/', views.UserListView.as_view(), name='user-list'),
    
      # Endpoint to retrieve the total number of users registered in the system. 
    path('admin/users/total/', views.total_users_view, name='total-users'),      
    
    
 
                        #TECHNICIAN URLS
    
    # API endpoint for authenticated users,to change their own password.
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    
    # API endpoint for requesting a password reset email.
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    
    # API endpoint for resetting the password using the token sent via email.
    path('password-reset/<uidb64>/<token>/', views.PasswordResetView.as_view(), name='password_reset_confirm'),
    
     #API endpoint for obtaining JWT tokens (access and refresh) with custom claims.
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('login/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
