from django.urls import path
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Registration endpoint for new users. This view handles user creation 
    # and initial setup, including password setting.
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    
    #path('login/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/google/', views.GoogleAuthView.as_view(), name='google_auth'),
    path('auth/apple/', views.AppleAuthView.as_view(), name='apple_auth'),
    
    # Login endpoint for existing users. This view authenticates a user and returns a JWT token
    # for subsequent authenticated requests.
    #path('login/', views.LoginView.as_view(), name='login'),
    
    # Endpoint for retrieving or updating user details. Access is restricted to authenticated users.
    # Users can only access their own user details unless additional permissions are configured.
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # Endpoint for retrieving or updating the profile associated with the authenticated user.
    # This view ensures that users can manage their personal information such as biography and birth date.
    path('user/profile/', views.UserProfileView.as_view(), name='user-profile'),
    
    # Endpoint for users to request a password reset. This typically involves sending an email
    # with a password reset link or token.
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    
    # Endpoint for users to confirm their password reset. This is where the actual password change
    # occurs, assuming a valid reset token is provided.
    path('password/reset/confirm/', views.PasswordResetView.as_view(), name='password-reset-confirm'),
    
    # Administrative endpoint to view a list of all users. Depending on the application's security
    # setup, access might be restricted to admin users.
    path('users/', views.UserListView.as_view(), name='user-list'),
    
    # Endpoint to retrieve the total number of users registered in the system. This might be used
    # for reporting or administrative purposes.
    path('users/total/', views.total_users_view, name='total-users'),
    
    path('login/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
