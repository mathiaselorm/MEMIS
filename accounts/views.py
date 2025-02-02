import logging

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.settings import api_settings
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import timedelta
from django.middleware.csrf import get_token

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from django_rest_passwordreset.views import ResetPasswordRequestToken

from .models import AuditLog
from .permissions import IsAdminOrSuperAdmin
from .serializers import (
    AuditLogSerializer,
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    RoleAssignmentSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from .tasks import send_password_change_email

User = get_user_model()
logger = logging.getLogger(__name__)







class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for registering a new user.
    Superusers can create any role, including Admins and Superadmins.
    Admins can only create Technicians and Admins but not Superadmins.
    Technicians cannot create any accounts.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="""
        Superusers can create any role, including Admins and Superadmins.
        Admins can only create Technicians and Admins but not Superadmins.
        Technicians cannot create any accounts.
        """,
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="User registered successfully. An email has been sent to set their password.",
                examples={
                    "application/json": {
                        "message": "User registered successfully. An email has been sent to set their password."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request",
                examples={
                    "application/json": {
                        "email": ["This email is already in use."],
                        "user_role": ["Invalid role specified."],
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "error": "An unexpected error occurred."
                    }
                }
            ),
        },
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()

        # Get the user's full name 
        full_name = user.get_full_name()

        # Log the user creation with full name
        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.ActionChoices.CREATE,
            target_user=user,
            details=_('User created: %(full_name)s') % {
                'full_name': full_name,
            }
        )
        logger.info(f"User {self.request.user.get_full_name()} created user with full name {full_name}.")

    def create(self, request, *args, **kwargs):
        # Override the create method to customize the response
        response = super().create(request, *args, **kwargs)
        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED
        )


class RoleAssignmentView(generics.UpdateAPIView):
    """
    API endpoint to assign or change user roles.
    Only Admins and Superadmins can assign roles.
    """
    queryset = User.objects.all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    lookup_field = 'id'  # or 'email' if preferred

    @swagger_auto_schema(
        operation_summary="Assign or change a user's role",
        operation_description="""
        Admins and Superadmins can assign or change a user's role. The available roles are:
        - Superadmin
        - Admin
        - Technician

        Admins cannot assign the Superadmin role. Technicians are not allowed to assign roles.
        """,
        request_body=RoleAssignmentSerializer,
        responses={
            200: openapi.Response(
                description="Role changed successfully.",
                examples={
                    "application/json": {
                        "message": "Role changed successfully for user john.doe@example.com.",
                        "new_role": "Admin"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Validation Error",
                examples={
                    "application/json": {
                        "new_role": ["Invalid role specified."]
                    }
                }
            ),
            403: openapi.Response(
                description="Permission Denied",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            user = self.get_object()
            
            full_name = user.get_full_name()
            
            # Log the role assignment
            AuditLog.objects.create(
                user=self.request.user,
                action=AuditLog.ActionChoices.ASSIGN_ROLE,
                target_user=user,
                details=_('Role changed to %(new_role)s for user %(full_name)s.') % {
                    'new_role': user.get_user_role_display(),
                    'full_name': full_name,
                }
            )
            logger.info(f"User {self.request.user.get_full_name()} changed role for user {full_name} to {user.get_user_role_display()}.")
        return response




class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens with custom claims.
    Generates access and refresh JWT tokens for authenticated users.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Obtain JWT tokens with custom claims",
        operation_description="""
        This API endpoint allows authenticated users to obtain JWT access and refresh tokens.
        The response will include the following:
        
        - Access Token: The token used for API authentication (set in an HTTP-only cookie).
        - Refresh Token: The token used to obtain new access tokens (set in an HTTP-only cookie).
        - CSRF Token: A token sent in a cookie for CSRF protection during client-side API requests.

        If the `remember_me` flag is set to `true`, the tokens will have extended lifetimes:
        
        Custom claims such as `email`, `first_name`, `last_name` and 'role' are included in the tokens.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The email of the user",
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="The password of the user",
                ),
                "remember_me": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    description="If set to true, the tokens will have extended lifetimes.",
                    default=False,
                ),
            },
            example={
                "email": "johna@gmail.com",
                "password": "examplepassword",
                "remember_me": True  # Include example with remember_me
            }
        ),
        responses={
            200: openapi.Response(
                description="Tokens obtained successfully. Tokens are set in HttpOnly cookies.",
                examples={
                    "application/json": {
                        "message": "Tokens set in cookies. CSRF token provided."
                    }
                },
                headers={
                    "Set-Cookie": openapi.Schema(
                        description="JWT Access and Refresh tokens are set in HttpOnly cookies, along with the CSRF token.",
                        type="string"
                    )
                }
            ),
            400: openapi.Response(
                description="Invalid credentials. The email or password provided is incorrect.",
                examples={
                    "application/json": {
                        "detail": "No active account found with the given credentials"
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized request. Authentication credentials were not provided or invalid.",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                }
            ),
        },
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        # Call the default TokenObtainPairView to generate tokens
        response = super().post(request, *args, **kwargs)
        secure_cookie = not settings.DEBUG  # Use secure cookies in production
        
        if response.status_code == 200:
            # Extract the tokens from the response
            tokens = response.data
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
             # Ensure the tokens exist
            if not access_token or not refresh_token:
                return Response({"error": "Failed to generate tokens."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Pull 'remember_me' from the request
            remember_me = bool(request.data.get('remember_me', False))
            
            access_token_lifetime = timedelta(minutes=15)
            refresh_token_lifetime = timedelta(days=5) if remember_me else timedelta(days=1)
                
            # Set tokens in HttpOnly cookies
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=secure_cookie, 
                samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
                max_age=access_token_lifetime.total_seconds(),  # Set cookie expiration to match access token
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=secure_cookie,  
                samesite='Lax' if settings.DEBUG else 'None', 
                max_age=refresh_token_lifetime.total_seconds(),  # 5 days if True, session-based if False
            )
            
            # Generate a CSRF token and send it in a cookie
            csrf_token = get_token(request)
            response.set_cookie(
                key='csrftoken',
                value=csrf_token,
                httponly=False,  # CSRF token needs to be readable by the frontend
                secure=secure_cookie, 
                samesite='Lax' if settings.DEBUG else 'None',  
                max_age=access_token_lifetime.total_seconds(), # Set cookie expiration to match access token
            )

            user_data = response.data.get('user', {})
            # Return a simplified JSON response
            response.data = {
                "message": "Tokens set in cookies. CSRF token provided.",
                "user": user_data  # Just use the data from the serializer
            }

            return response
                    

class CustomTokenRefreshView(APIView):
    """
    API endpoint for refreshing JWT access tokens.
    Uses the refresh token stored in cookies to generate a new access token.
    """

    @swagger_auto_schema(
        operation_summary="Refresh JWT access token",
        operation_description="""
        This API endpoint allows users to refresh their JWT access token using the refresh token stored in HttpOnly cookies.
        The response will include:
        
        - A new access token (set in an HttpOnly cookie).
        - A new refresh token (if enabled and set in an HttpOnly cookie).
        - A new CSRF token (sent in a readable cookie for frontend protection).
        
        No request body is required as the refresh token is retrieved from the cookies.
        """,
        request_body=None,  # No request body required
        responses={
            200: openapi.Response(
                description="Access token refreshed successfully. Tokens are set in HttpOnly cookies.",
                examples={
                    "application/json": {
                        "message": "New access token set in HttpOnly cookie."
                    }
                },
                headers={
                    "Set-Cookie": openapi.Schema(
                        description="JWT tokens and CSRF token set in HttpOnly cookies.",
                        type="string"
                    )
                }
            ),
            400: openapi.Response(
                description="Refresh token not found or invalid.",
                examples={
                    "application/json": {
                        "error": "Refresh token not found."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized. The refresh token may have expired or been blacklisted.",
                examples={
                    "application/json": {
                        "detail": "Token is invalid or expired."
                    }
                }
            ),
        },
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        secure_cookie = not settings.DEBUG
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            old_refresh = RefreshToken(refresh_token)
            user_id = old_refresh.payload.get('user_id')
            if not user_id:
                return Response({"error": "Invalid refresh token claims."}, status=status.HTTP_400_BAD_REQUEST)

            # Validate user existence
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"error": "User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

            # Extract custom claims
            custom_claims = {
                k: v for k, v in old_refresh.payload.items()
                if k not in ['token_type', 'exp', 'iat', 'jti']
            }
            remember_me = custom_claims.get('remember_me', False)

            # Generate new access token
            access_token_lifetime = timedelta(minutes=15)
            new_access_token = old_refresh.access_token
            new_access_token.set_exp(lifetime=access_token_lifetime)
            for k, v in custom_claims.items():
                new_access_token[k] = v

            # Rotate refresh token if enabled
            if api_settings.ROTATE_REFRESH_TOKENS:
                new_refresh_token = RefreshToken.for_user(user)
                refresh_token_lifetime = timedelta(days=5) if remember_me else timedelta(days=1)
                new_refresh_token.set_exp(lifetime=refresh_token_lifetime)
                for k, v in custom_claims.items():
                    new_refresh_token[k] = v

                # Blacklist the old refresh token
                old_refresh.blacklist()

                # Return the new refresh token in a cookie
                response = Response(
                    {"message": "New access token and refresh token set in HttpOnly cookie."},
                    status=status.HTTP_200_OK
                )
                response.set_cookie(
                    key='refresh_token',
                    value=str(new_refresh_token),
                    httponly=True,
                    secure=secure_cookie,
                    samesite='Lax' if settings.DEBUG else 'None',
                    max_age=refresh_token_lifetime.total_seconds(),
                )
            else:
                response = Response(
                    {"message": "New access token set in HttpOnly cookie."},
                    status=status.HTTP_200_OK
                )

            # Set new access token in cookie
            response.set_cookie(
                key='access_token',
                value=str(new_access_token),
                httponly=True,
                secure=secure_cookie,
                samesite='Lax' if settings.DEBUG else 'None',
                max_age=access_token_lifetime.total_seconds(),
            )

            # Set new CSRF token
            csrf_token = get_token(request)
            response.set_cookie(
                key='csrftoken',
                value=csrf_token,
                httponly=False,
                secure=secure_cookie,
                samesite='Lax' if settings.DEBUG else 'None',
                max_age=access_token_lifetime.total_seconds(),
            )
            
            # #Return the new access token for debugging in development
            # if settings.DEBUG:
            #     response.data['access_token'] = str(new_access_token)
            #     response.data['refresh_token'] = str(new_refresh_token) if api_settings.ROTATE_REFRESH_TOKENS else None

            return response

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    
    
# class PasswordResetRequestThrottle(AnonRateThrottle):
#     rate = '5/hour'

class CustomPasswordResetRequestView(ResetPasswordRequestToken):
    throttle_classes = []
    
    def get_user_by_email(self, email):
        # Use a case-insensitive lookup and strip any whitespace
        email = email.strip()
        try:
            return User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise ValidationError("We couldn't find an account associated with that email. Please try a different e-mail address.")


class PasswordChangeView(generics.UpdateAPIView):
    """
    An endpoint for changing password for authenticated users.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_description="Change password for the authenticated user.",
        responses={
            200: openapi.Response(
                description="Password changed successfully.",
                examples={
                    "application/json": {"detail": "Your password has been changed successfully."}
                }
            ),
            400: openapi.Response(
                description="Bad Request due to invalid input.",
                examples={
                    "application/json": {
                        "old_password": ["The old password is incorrect."],
                        "new_password": ["This password is too short.", "This password is too common."]
                    }
                }
            )
        },
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, description="Old Password", format="password"),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, description="New Password", format="password"),
            },
            required=['old_password', 'new_password']
        ),
        security=[{'Bearer': []}], 
        tags=['User Account Management']
    )
    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = self.get_object()
            serializer.save()

            # Send password change email notification
            send_password_change_email(user.id)

            # Log the password change
            AuditLog.objects.create(
                user=user,
                action=AuditLog.ActionChoices.UPDATE,
                target_user=user,
                details=_('User changed password.')
            )
            logger.info(f"User {user.get_full_name()} changed their password.")

            return Response({"detail": _("Your password has been changed successfully.")}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete the details of a user.
    Admins and Superusers can manage Technician profiles, but they cannot update passwords.
    Technicians cannot edit their own profiles.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    def get_object(self):
        """
        Retrieve the user object.
        Prevent Technicians from editing their own profiles.
        """
        obj = super().get_object()
        if self.request.user.user_role == User.UserRole.TECHNICIAN and self.request.user == obj:
            raise PermissionDenied(_("You cannot update your own profile. Contact an Admin for changes."))
        return obj

    def update(self, request, *args, **kwargs):
        """
        Update user details excluding uneditable fields.
        """
        user = self.get_object()

        # Filter out uneditable fields if they somehow bypassed serializer exclusion
        uneditable_fields = ['password', 'is_superuser']
        data = request.data.copy()
        for field in uneditable_fields:
            if field in data:
                data.pop(field)

        # Use serializer with partial update enabled
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Log and audit the update
        AuditLog.objects.create(
            user=self.request.user,
            action=AuditLog.ActionChoices.UPDATE,
            target_user=user,
            details=_('User details updated.')
        )
        logger.info(f"User {self.request.user.get_full_name()} updated details for user {user.get_full_name()}.")

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Delete the user account.
        """
        user = self.get_object()

        # Log and audit before deletion
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ActionChoices.DELETE,
            target_user=user,
            details=_("User account deleted.")
        )
        logger.info(f"User {request.user.get_full_name()} deleted user {user.get_full_name()}.")

        # Perform deletion by calling the superclass method
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Retrieve User Details",
        operation_description="Retrieve the details of a specific user. Only Admins and Superadmins can perform this operation.",
        responses={
            200: openapi.Response(
                description="User details retrieved successfully.",
                examples={
                    "application/json": {
                        "id": 1,
                        "email": "johndoe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone_number": "+1234567890",
                        "user_role": "Admin",
                        "date_joined": "2024-01-01T12:00:00Z",
                        "last_login": "2024-01-10T10:00:00Z"
                    }
                }
            ),
            403: openapi.Response(
                description="Permission Denied",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
            404: openapi.Response(
                description="User Not Found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def get(self, request, *args, **kwargs):
        """Retrieve the details of a user."""
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update User Details",
        operation_description="Update the details of a specific user. Password and superuser status cannot be updated.",
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="User updated successfully.",
                examples={
                    "application/json": {
                        "id": 1,
                        "email": "johndoe@example.com",
                        "first_name": "John",
                        "last_name": "Doe",
                        "phone_number": "+1234567890",
                        "user_role": "Admin",
                        "date_joined": "2024-01-01T12:00:00Z",
                        "last_login": "2024-01-10T10:00:00Z"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Validation Error",
                examples={
                    "application/json": {
                        "first_name": ["This field is required."],
                        "email": ["This email is already in use."]
                    }
                }
            ),
            403: openapi.Response(
                description="Permission Denied",
                examples={
                    "application/json": {
                        "detail": "You cannot update your own profile. Contact an Admin for changes."
                    }
                }
            ),
            404: openapi.Response(
                description="User Not Found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def put(self, request, *args, **kwargs):
        """Update the details of a user, excluding password."""
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete User",
        operation_description="Delete a user. Only Admins and Superadmins can delete user accounts.",
        responses={
            204: openapi.Response(
                description="User deleted successfully.",
                examples={
                    "application/json": {
                        "detail": "User account deleted successfully."
                    }
                }
            ),
            403: openapi.Response(
                description="Permission Denied",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
            404: openapi.Response(
                description="User Not Found",
                examples={
                    "application/json": {
                        "detail": "Not found."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def delete_user(self, request, *args, **kwargs):
        """Delete the user account."""
        return self.destroy(request, *args, **kwargs)
    
    
    

@swagger_auto_schema(
    method='post',
    operation_summary="Log Out User",
    operation_description="""
    Logs out the user by blacklisting the refresh token (if in use) and clearing relevant cookies.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token (optional)"),
        },
        required=[]
    ),
    responses={
        200: openapi.Response(
            description="Logged out successfully.",
            examples={
                "application/json": {
                    "message": "Logged out successfully."
                }
            }
        ),
        400: openapi.Response(
            description="Bad Request - No refresh token found or invalid token.",
            examples={
                "application/json": {
                    "error": "Refresh token not found"
                }
            }
        ),
    },
    tags=["Authentication"]
)
@api_view(['POST'])
def logout_view(request):
    """
    Logs out the user by blacklisting the refresh token if present,
    then deletes the access, refresh, and CSRF cookies.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({"error": "Refresh token not found in cookies"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()  # Blacklist the refresh token
        
        # Log the user logout
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ActionChoices.LOGOUT,
            target_user=request.user,
            details=_('User logged out.')
        )
        logger.info(f"User {request.user.get_full_name()} logged out.")
        
    except Exception as e:
        # Typically occurs if the token is invalid or already blacklisted
        logger.error(f"Error during logout for user {request.user.email}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response = Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
    # Clear cookies
    response.delete_cookie('refresh_token')
    response.delete_cookie('access_token')
    response.delete_cookie('csrftoken')
    return response
    

class UserListView(ListAPIView):
    """
    List users based on the role of the requester.
    Superusers and Admins can see all users.
    Technicians cannot access this view.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    @swagger_auto_schema(
        operation_summary="List Users",
        operation_description="""
        Lists users based on the role of the requester.
        Superusers and Admins can see all users.
        Technicians are restricted from accessing this view.
        """,
        responses={
            200: openapi.Response(
                description="List of users retrieved successfully.",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "email": "admin@example.com",
                            "first_name": "Admin",
                            "last_name": "User",
                            "phone_number": "+123456789",
                            "user_role": "Admin",
                            "date_joined": "2023-01-01T12:00:00Z",
                            "last_login": "2023-01-02T12:00:00Z"
                        },
                        {
                            "id": 2,
                            "email": "technician@example.com",
                            "first_name": "Technician",
                            "last_name": "User",
                            "phone_number": "+987654321",
                            "user_role": "Technician",
                            "date_joined": "2023-01-01T12:00:00Z",
                            "last_login": "2023-01-02T12:00:00Z"
                        }
                    ]
                }
            ),
            403: openapi.Response(
                description="Permission Denied - Technicians cannot view users.",
                examples={
                    "application/json": {
                        "detail": "You do not have permission to view this resource."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"User {request.user.get_full_name()} accessed the user list.")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_role == User.UserRole.ADMIN:
            # Superusers and Admins can see all users except superusers
            return User.objects.filter(is_superuser=False).order_by('id')
        else:
            # Technicians cannot see any users
            raise PermissionDenied(detail="You do not have permission to view this resource.")
        
        
@swagger_auto_schema(
        method='get',
    operation_summary="Get Total Number of Users",
    operation_description="""
    Retrieve the total number of users.
    Only accessible by Admins and Superusers.
    Technicians do not have access to this resource.
    """,
    responses={
        200: openapi.Response(
            description="Total number of users retrieved successfully.",
            examples={
                "application/json": {
                    "total_users": 120  # Example count
                }
            }
        ),
        403: openapi.Response(
            description="Permission Denied - Technicians cannot access this resource.",
            examples={
                "application/json": {
                    "detail": "You do not have permission to view this resource."
                }
            }
        ),
    },
    tags=["User Management"]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsAdminOrSuperAdmin])
def total_users_view(request):
    """
    Get the total number of users.
    Only accessible by Admins and Superusers.
    """
    total_users = User.objects.count()
    logger.info(f"User {request.user.get_full_name()} retrieved total user count: {total_users}.")
    return Response({"total_users": total_users})


class AuditLogView(ListAPIView):
    """
    API view to list audit logs.
    Only accessible by Admins and Superadmins.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    def get_queryset(self):
        logger.info(f"User {self.request.user.get_full_name()} accessed the audit logs.")
        return AuditLog.objects.all().order_by('-timestamp')
