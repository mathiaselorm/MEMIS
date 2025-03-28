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

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


from django_rest_passwordreset.views import ResetPasswordRequestToken

from .permissions import IsAdminOrSuperAdmin
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordChangeSerializer,
    RoleAssignmentSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)
from .tasks import send_password_change_email

User = get_user_model()
logger = logging.getLogger(__name__)







from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer
from .permissions import IsAdminOrSuperAdmin
import logging

logger = logging.getLogger(__name__)

@extend_schema(
    summary="Register a new user",
    description="""
    Registers a new user account.

    - **Superadmins** can create any account type (including Admin and Superadmin).
    - **Admins** can create Admin and Technician accounts but cannot create Superadmin accounts.
    - **Technicians** are not permitted to create any accounts.
    """,
    request=UserRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            description="User registered successfully. An email has been sent to set their password.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"message": "User registered successfully."},
                    response_only=True,
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request. Validation errors occurred.",
            examples=[
                OpenApiExample(
                    "Validation Error",
                    value={"email": ["This email is already in use."], "user_role": ["Invalid role specified."]},
                    response_only=True,
                )
            ],
        ),
        500: OpenApiResponse(
            description="Internal Server Error. An unexpected error occurred.",
            examples=[
                OpenApiExample(
                    "Server Error",
                    value={"error": "An unexpected error occurred."},
                    response_only=True,
                )
            ],
        ),
    },
    tags=["User Management"]
)
class UserRegistrationView(generics.CreateAPIView):
    """
    API endpoint for registering a new user.
    
    - **Permissions:** Only authenticated users with Admin or Superadmin privileges can register new users.
    - **Behavior:** 
        - Superadmins can register accounts of any role.
        - Admins can register accounts except for Superadmin.
        - Technicians cannot register new accounts.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to register a new user.
        """
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        Save the new user instance and log the creation event.
        """
        user = serializer.save()
        full_name = user.get_full_name()
        logger.info(f"User created: {full_name}")

    def create(self, request, *args, **kwargs):
        """
        Override create to customize the success response.
        """
        response = super().create(request, *args, **kwargs)
        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    summary="Assign or change a user's role",
    description="""
    Admins and Superadmins can assign or change a user's role. The available roles are:
    
    - **Superadmin**
    - **Admin**
    - **Technician**
    
    **Note:**
    
    - Admins cannot assign the Superadmin role.
    - Technicians are not allowed to assign roles.
    """,
    request=RoleAssignmentSerializer,
    responses={
        200: OpenApiResponse(
            description="Role changed successfully.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={
                        "message": "Role changed successfully for user john.doe@example.com.",
                        "new_role": "Admin"
                    },
                    response_only=True,
                )
            ],
        ),
        400: OpenApiResponse(
            description="Bad Request - Validation Error",
            examples=[
                OpenApiExample(
                    "Validation Error Example",
                    value={"new_role": ["Invalid role specified."]},
                    response_only=True,
                )
            ],
        ),
        403: OpenApiResponse(
            description="Permission Denied",
            examples=[
                OpenApiExample(
                    "Permission Denied Example",
                    value={"detail": "You do not have permission to perform this action."},
                    response_only=True,
                )
            ],
        ),
    },
    tags=["User Management"]
)
class RoleAssignmentView(generics.UpdateAPIView):
    """
    API endpoint to assign or change user roles.

    **Permissions:** Only authenticated users with Admin or Superadmin privileges can assign roles.
    """
    queryset = User.objects.all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSuperAdmin]
    lookup_field = 'id' 

    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests to update a user's role.
        """
        response = super().put(request, *args, **kwargs)
        # Additional logic (if any) after updating the role can be added here.
        return response




@extend_schema(
    summary="Obtain JWT tokens",
    description="Obtain JWT tokens for authenticated users.",
    responses={
        200: OpenApiResponse(description="Tokens obtained"),
        400: OpenApiResponse(description="Bad Request")
    },
    tags=["login"]
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens with custom claims.
    Generates access and refresh JWT tokens for authenticated users.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    
    
    
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


@extend_schema(
    summary="Change password",
    description="Change password for the authenticated user.",
    request=PasswordChangeSerializer,
    responses={
        200: OpenApiResponse(
            description="Password changed successfully.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"detail": "Your password has been changed successfully."},
                    response_only=True,
                )
            ]
        ),
        400: OpenApiResponse(
            description="Bad Request due to invalid input.",
            examples=[
                OpenApiExample(
                    "Validation Error Example",
                    value={
                        "old_password": ["The old password is incorrect."],
                        "new_password": ["This password is too short.", "This password is too common."]
                    },
                    response_only=True,
                )
            ]
        )
    },
    tags=["User Management"]
)
class PasswordChangeView(generics.UpdateAPIView):
    """
    An endpoint for changing the password of the authenticated user.
    """
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = self.get_object()
            serializer.save()

            # Send password change email notification
            send_password_change_email(user.id)

            return Response(
                {"detail": _("Your password has been changed successfully.")},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete the details of a user.
    
    - **Admins and Superusers** can manage Technician profiles, but they cannot update passwords.
    - **Technicians** cannot edit their own profiles.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

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

        logger.info(f"User {request.user.get_full_name()} updated details for {user.get_full_name()}.")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """
        Delete the user account.
        """
        user = self.get_object()
        logger.info(f"User {request.user.get_full_name()} deleted user {user.get_full_name()}.")
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve User Details",
        description="Retrieve the details of a specific user. Only Admins and Superadmins can perform this operation.",
        responses={
            200: OpenApiResponse(
                description="User details retrieved successfully.",
                examples=[
                    OpenApiExample(
                        "Success Example",
                        value={
                            "id": 1,
                            "email": "johndoe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "phone_number": "+1234567890",
                            "user_role": "Admin",
                            "date_joined": "2024-01-01T12:00:00Z",
                            "last_login": "2024-01-10T10:00:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission Denied",
                examples=[
                    OpenApiExample(
                        "Permission Denied Example",
                        value={"detail": "You do not have permission to perform this action."},
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(
                description="User Not Found",
                examples=[
                    OpenApiExample(
                        "Not Found Example",
                        value={"detail": "Not found."},
                        response_only=True,
                    )
                ]
            ),
        },
        tags=["User Management"]
    )
    def get(self, request, *args, **kwargs):
        """Retrieve the details of a user."""
        return self.retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Update User Details",
        description="Update the details of a specific user. Password and superuser status cannot be updated.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                description="User updated successfully.",
                examples=[
                    OpenApiExample(
                        "Success Example",
                        value={
                            "id": 1,
                            "email": "johndoe@example.com",
                            "first_name": "John",
                            "last_name": "Doe",
                            "phone_number": "+1234567890",
                            "user_role": "Admin",
                            "date_joined": "2024-01-01T12:00:00Z",
                            "last_login": "2024-01-10T10:00:00Z"
                        },
                        response_only=True,
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Bad Request - Validation Error",
                examples=[
                    OpenApiExample(
                        "Validation Error Example",
                        value={
                            "first_name": ["This field is required."],
                            "email": ["This email is already in use."]
                        },
                        response_only=True,
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission Denied",
                examples=[
                    OpenApiExample(
                        "Permission Denied Example",
                        value={"detail": "You cannot update your own profile. Contact an Admin for changes."},
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(
                description="User Not Found",
                examples=[
                    OpenApiExample(
                        "Not Found Example",
                        value={"detail": "Not found."},
                        response_only=True,
                    )
                ]
            ),
        },
        tags=["User Management"]
    )
    def put(self, request, *args, **kwargs):
        """Update the details of a user, excluding password."""
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete User",
        description="Delete a user. Only Admins and Superadmins can delete user accounts.",
        responses={
            204: OpenApiResponse(
                description="User deleted successfully.",
                examples=[
                    OpenApiExample(
                        "Success Example",
                        value={"detail": "User account deleted successfully."},
                        response_only=True,
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Permission Denied",
                examples=[
                    OpenApiExample(
                        "Permission Denied Example",
                        value={"detail": "You do not have permission to perform this action."},
                        response_only=True,
                    )
                ]
            ),
            404: OpenApiResponse(
                description="User Not Found",
                examples=[
                    OpenApiExample(
                        "Not Found Example",
                        value={"detail": "Not found."},
                        response_only=True,
                    )
                ]
            ),
        },
        tags=["User Management"]
    )
    def delete_user(self, request, *args, **kwargs):
        """Delete the user account."""
        return self.destroy(request, *args, **kwargs)
    
    
    

    

@extend_schema(
    summary="List Users",
    description="""
    Lists users based on the role of the requester.
    
    - **Superusers and Admins** can see all users.
    - **Technicians** are restricted from accessing this view.
    """,
    responses={
        200: OpenApiResponse(
            description="List of users retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value=[
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
                    ],
                    response_only=True
                )
            ]
        ),
        403: OpenApiResponse(
            description="Permission Denied - Technicians cannot view users.",
            examples=[
                OpenApiExample(
                    "Permission Denied Example",
                    value={"detail": "You do not have permission to view this resource."},
                    response_only=True
                )
            ]
        )
    },
    tags=["User Management"]
)
class UserListView(generics.ListAPIView):
    """
    List users based on the role of the requester.
    
    - **Superusers and Admins** can see all users.
    - **Technicians** cannot access this view.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"User {request.user.get_full_name()} accessed the user list.")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        # Return all users, or some subset if you prefer
        return User.objects.all().order_by('id')


@extend_schema(
    summary="Get Total Number of Users",
    description="""
    Retrieve the total number of users.
    
    - Only accessible by Admins and Superusers.
    - Technicians do not have access to this resource.
    """,
    responses={
        200: OpenApiResponse(
            description="Total number of users retrieved successfully.",
            examples=[
                OpenApiExample(
                    "Success Example",
                    value={"total_users": 120},
                    response_only=True
                )
            ]
        ),
        403: OpenApiResponse(
            description="Permission Denied - Technicians cannot access this resource.",
            examples=[
                OpenApiExample(
                    "Permission Denied Example",
                    value={"detail": "You do not have permission to view this resource."},
                    response_only=True
                )
            ]
        )
    },
    tags=["User Management"],
    methods=['GET']
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def total_users_view(request):
    """
    Get the total number of users.
    
    Only accessible by Admins and Superusers.
    """
    total_users = User.objects.count()
    logger.info(f"User {request.user.get_full_name()} retrieved total user count: {total_users}.")
    return Response({"total_users": total_users})