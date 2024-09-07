from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Registration endpoint for new users. This view handles user creation 
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    #API endpoint for authenticating via Google OAuth2 using Firebase.
    path('auth/google/', views.GoogleAuthView.as_view(), name='google_auth'),    
  
    
    # Endpoint for retrieving or updating user details. 
    # Superusers and Admins can update user profiles, except for passwords and superuser status.
    # Regular users are restricted from editing their profiles.
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # API endpoint for authenticated users (regular, Admin, or SuperAdmin) to change their own password.
    path('password/change/', views.PasswordChangeView.as_view(), name='password-change'),
    
    # API endpoint for requesting a password reset email.
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    
    # API endpoint for resetting the password using the token sent via email.
    path('password-reset/<uidb64>/<token>/', views.PasswordResetView.as_view(), name='password_reset_confirm'),
    
    # API endpoint for listing users.
    # Superusers can see all users.
    #Admins can only see regular users (user_type=3).
    #Regular users have no access to this endpoint.
    path('users/', views.UserListView.as_view(), name='user-list'),
    
    # Endpoint to retrieve the total number of users registered in the system. 
    path('users/total/', views.total_users_view, name='total-users'),
    
     #API endpoint for obtaining JWT tokens (access and refresh) with custom claims.
    path('login/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
