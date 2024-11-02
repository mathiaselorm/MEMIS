import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, permissions, status, views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.exceptions import ValidationError

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
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    
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

        

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the details of a user.
    Admins and Superusers can update Technician profiles, but they cannot update their passwords.
    Technicians users cannot edit their own profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    def get_object(self):
        obj = super().get_object()
        if self.request.user.user_role == User.UserRole.TECHNICIAN and self.request.user == obj:
            raise PermissionDenied(_("You cannot update your own profile. Contact an Admin for changes."))
        return obj

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # Prevent editing of certain fields
        non_editable_fields = ['password', 'is_superuser', 'email', 'user_role']
        for field in non_editable_fields:
            if field in request.data:
                request.data.pop(field)

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            # Log the user update
            AuditLog.objects.create(
                user=self.request.user,
                action=AuditLog.ActionChoices.UPDATE,
                target_user=user,
                details=_('User details updated.')
            )
            logger.info(f"User {self.request.user.get_full_name()} updated details for user {user.get_full_name()}.")

        return response

    @swagger_auto_schema(
        operation_summary="Retrieve User Details",
        operation_description="""
        Retrieve the details of a specific user. Only Admins and Superadmins can perform this operation.
        """,
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
        },
        tags=["User Management"]
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieve the details of a user.
        """
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update User Details",
        operation_description="""
        Update the details of a specific user. Password and superuser status cannot be updated using this endpoint.
        Only Admins and Superadmins can update user details.
        """,
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
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def put(self, request, *args, **kwargs):
        """
        Update the details of a user, excluding password.
        """
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update User Details",
        operation_description="""
        Partially update the details of a specific user. Password and superuser status cannot be updated using this endpoint.
        Only Admins and Superadmins can perform this action.
        """,
        request_body=UserSerializer,
        responses={
            200: openapi.Response(
                description="User details partially updated successfully.",
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
                        "detail": "You do not have permission to perform this action."
                    }
                }
            ),
        },
        tags=["User Management"]
    )
    def patch(self, request, *args, **kwargs):
        """
        Partially update the details of a user.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    


 

@swagger_auto_schema(
    method='post',
    operation_summary="Log Out User",
    operation_description="""
    Logs out the user by blacklisting the refresh token.
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'refresh_token': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
        },
        required=['refresh_token']
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
            description="Bad Request - No refresh token provided or invalid token.",
            examples={
                "application/json": {
                    "error": "No refresh token provided"
                }
            }
        ),
    },
    tags=["Authentication"]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    View to log out the user by blacklisting the refresh token.
    """
    refresh = request.data.get('refresh')
    if not refresh:
        return Response({"error": "No refresh token provided"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Blacklist the refresh token
        token = RefreshToken(refresh)
        token.blacklist()

        # Log the logout action
        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.ActionChoices.LOGOUT,
            target_user=request.user,
            details=_('User logged out.')
        )
        logger.info(f"User {request.user.get_full_name()} logged out.")

        return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)

    except Exception as e:
        user_full_name = request.user.get_full_name() if request.user.is_authenticated else 'Anonymous'
        logger.error(f"Error during logout for user {user_full_name}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    


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
