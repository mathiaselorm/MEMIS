from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework import generics, status, views, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.middleware.csrf import get_token
from rest_framework_simplejwt.settings import api_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .permissions import IsAdminUser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.template import TemplateDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .serializers import *
from .tasks import *


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
import logging




# Secure cookie setting for production
secure_cookie = not settings.DEBUG  # Set secure=True in production

# Token lifetimes (extracted from SimpleJWT settings)
access_token_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
refresh_token_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()


User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegistrationView(views.APIView):
    """
    API endpoint for registering a new user.
    Superusers can create any role, including Admins and Superadmins.
    Admins can only create Technicians and Admins but not Superadmins.
    Technicians cannot create any accounts.
    """
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]  # Only Admins and Superusers can access

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
                        "password": ["Password must be at least 8 characters long."],
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "error": "Email template not found."
                    }
                }
            )
        },
        tags=["Authentication"]
    )
    def post(self, request, *args, **kwargs):
        # Pass the request to the serializer for context
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        
        # Validate the serializer
        if serializer.is_valid():
            try:
                # Save the user and send the account creation email
                user = serializer.save()
                
                # Log the success and proceed with sending email
                logger.info(f"User created successfully: {user.email}")

                # Prepare the response with user details and tokens
                return Response({
                    # 'user': UserSerializer(user).data,
                    'message': "User registered successfully. An email has been sent to set their password."
                }, status=status.HTTP_201_CREATED)

            except TemplateDoesNotExist as e:
                logger.error(f"Template not found: {e}")
                return Response({"error": "Email template not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Error during user creation: {e}")
                return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        # If serializer is not valid, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleAssignmentView(APIView):
    """
    API endpoint to assign or change user roles.
    Only Admins and Superadmins can assign roles.
    """
    permission_classes = [IsAdminUser]  # Only Admins or Superadmins can access this view

    @swagger_auto_schema(
        operation_summary="Assign or change a user's role",
        operation_description="""
        Only Admins and Superadmins can assign or change a user's role.
        Valid roles include: 'Superadmin', 'Admin', 'Technician'.
        """,
        request_body=RoleAssignmentSerializer,
        responses={
            200: openapi.Response(
                description="Role changed successfully.",
                examples={
                    "application/json": {
                        "message": "Role changed successfully for user john_doe.",
                        "new_role": "Admin"
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Validation Error",
                examples={
                    "application/json": {
                        "username": ["User with this username does not exist."],
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
        tags=["authentication"]
    )
    def post(self, request, *args, **kwargs):
        # Validate the request data with the RoleAssignmentSerializer
        serializer = RoleAssignmentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            # Call the serializer's update method to handle the role assignment
            user = serializer.save()

            return Response({
                "message": f"Role changed successfully for user {user.username}.",
                "new_role": user.get_user_role_display(),
            }, status=status.HTTP_200_OK)

        # If serializer is not valid, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens with custom claims.
    Generates access and refresh JWT tokens for authenticated users and sets them in HttpOnly cookies.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Obtain JWT access and refresh tokens",
        operation_description="""
        Authenticated users can obtain JWT access and refresh tokens. 
        The tokens are set in HttpOnly cookies.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["email", "password"],
            properties={
                "email": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's email address",
                    example="user@example.com"
                ),
                "password": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's password",
                    example="password123"
                ),
            },
            example={
                "email": "user@example.com",
                "password": "password123"
            }
        ),
        responses={
            200: openapi.Response(
                description="Tokens obtained successfully and set in HttpOnly cookies.",
                examples={
                    "application/json": {
                        "message": "Access token and refresh token set in HttpOnly cookie."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Failed to generate tokens.",
                examples={
                    "application/json": {
                        "error": "Failed to generate tokens."
                    }
                }
            ),
            401: openapi.Response(
                description="Unauthorized - Invalid credentials.",
                examples={
                    "application/json": {
                        "error": "Invalid credentials."
                    }
                }
            ),
        },
        tags=["authentication"]
    )
    def post(self, request, *args, **kwargs):
        # Call the default TokenObtainPairView to generate tokens
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Extract the tokens from the response
            tokens = response.data
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            csrf_token = get_token(request)

            # Ensure the tokens exist
            if not access_token or not refresh_token:
                return Response({"error": "Failed to generate tokens."}, status=status.HTTP_400_BAD_REQUEST)
            
            # response = Response({"message": "Access token and refresh token set in HttpOnly cookie."}, status=status.HTTP_200_OK)
            
            # Set access token in HttpOnly cookie
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,
                secure=secure_cookie,  # Ensure secure cookie in production
                samesite='Lax' if settings.DEBUG else 'None',  # SameSite attribute
                max_age=access_token_lifetime,  # Expiration matches access token lifetime
            )

            # Set refresh token in HttpOnly cookie
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=secure_cookie,  # Ensure secure cookie in production
                samesite='Lax' if settings.DEBUG else 'None',  # SameSite attribute
                max_age=refresh_token_lifetime,  # Expiration matches refresh token lifetime
            )

            response.set_cookie(
                key='csrftoken',
                value=csrf_token,
                httponly=False,  # Needs to be readable by the frontend
                secure=secure_cookie,  # Set secure=True in production
                samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
                max_age=access_token_lifetime,  # Set cookie expiration to match access token
            )
            
            return response

        # If the request fails (e.g., wrong credentials)
        return Response({"error": "Invalid credentials."}, status=response.status_code)
    

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
                        description="JWT Access token and CSRF token set in cookies.",
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
        # Get the refresh token from the cookies
        refresh_token = request.COOKIES.get('refresh_token')
        secure_cookie = not settings.DEBUG  # Set secure=True in production

        if not refresh_token:
            return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Validate the refresh token
            refresh = RefreshToken(refresh_token)

            # Extract custom claims from refresh token payload, excluding standard claims
            custom_claims = {key: value for key, value in refresh.payload.items() 
                             if key not in ['token_type', 'exp', 'iat', 'jti']}

            # Generate a new access token
            new_access_token = refresh.access_token

            # Add custom claims to the new access token
            for key, value in custom_claims.items():
                new_access_token[key] = value

            # Handle refresh token rotation if enabled
            if api_settings.ROTATE_REFRESH_TOKENS:
                # Generate a new refresh token
                new_refresh_token = RefreshToken()

                # Add custom claims to the new refresh token
                for key, value in custom_claims.items():
                    new_refresh_token[key] = value

                # Set the new refresh token in HttpOnly cookie
                response = Response({"message": "New access token and refresh token set in HttpOnly cookie."}, status=status.HTTP_200_OK)
                response.set_cookie(
                    key='refresh_token',
                    value=str(new_refresh_token),  # Use the new refresh token
                    httponly=True,
                    secure=secure_cookie,  # Set secure=True in production
                    samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
                    max_age=refresh_token_lifetime,  # Set cookie expiration to match refresh token
                )

                # Blacklist the old refresh token after the new one is securely sent
                refresh.blacklist()
            else:
                response = Response({"message": "New access token set in HttpOnly cookie."}, status=status.HTTP_200_OK)

            # Set the new access token in HttpOnly cookie
            response.set_cookie(
                key='access_token',
                value=str(new_access_token),
                httponly=True,
                secure=secure_cookie,  # Set secure=True in production
                samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
                max_age=access_token_lifetime,  # Set cookie expiration to match access token
            )

            # Generate and set a new CSRF token
            csrf_token = get_token(request)
            response.set_cookie(
                key='csrftoken',
                value=csrf_token,
                httponly=False,  # Needs to be readable by the frontend
                secure=secure_cookie,  # Set secure=True in production
                samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
                max_age=access_token_lifetime,  # Set cookie expiration to match access token
            )

            # Return the new access token for debugging in development
            if settings.DEBUG:
                response.data['access_token'] = str(new_access_token)

            return response

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
        

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the details of a user.
    Admins and Superusers can update user profiles, but they cannot update passwords.
    Regular users cannot edit their profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]

    def get_object(self):
        """
        Allow Admins and Superusers to edit any user profile, but regular users cannot edit their own profile.
        """
        obj = super().get_object()
        if self.request.user.user_role == 3:  # Regular user
            raise PermissionDenied("You cannot update your own profile. Contact an Admin for changes.")
        return obj

    def update(self, request, *args, **kwargs):
        user = self.get_object()

        # Prevent Admins and Superusers from editing password via this view
        non_editable_fields = ['password', 'is_superuser']

        # Remove any fields that shouldn't be editable
        for field in non_editable_fields:
            if field in request.data:
                request.data.pop(field)

        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Retrieve User Details")
    def get(self, request, *args, **kwargs):
        """
        Retrieve the details of a user.
        """
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update User Details")
    def put(self, request, *args, **kwargs):
        """
        Update the details of a user, excluding password.
        """
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Partially Update User Details")
    def patch(self, request, *args, **kwargs):
        """
        Partially update the details of a user.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    
class PasswordChangeView(views.APIView):
    """
    Allow any authenticated user (regular user, admin, or superadmin) to update their own password.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change User Password",
        request_body=PasswordResetSerializer,  # Use the same serializer to capture password fields
        responses={200: "Password Updated", 400: "Bad Request"}
    )
    def post(self, request):
        """
        Handle password change for authenticated users.
        """
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user  # Get the currently authenticated user
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)  # Update the user's password
            user.save()
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(views.APIView):
    """
    Request a password reset via email.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Request Password Reset", request_body=PasswordResetRequestSerializer)
    def post(self, request):
        """
        Handle password reset request.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            frontend_url = serializer.validated_data['frontend_url']  # Get the frontend URL from the request

            
            user = User.objects.filter(email=email).first()
            
            if user:
                # Generate a one-time-use token and a UID
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Construct the password reset URL using the frontend URL
                reset_url = f"{frontend_url}/api/password-reset/{uid}/{token}/"

            
                try:
                    # Offload email sending to background or send synchronously
                    send_password_reset_email(user.id, reset_url)
                except Exception as e:
                    logger.error(f"Failed to send email: {e}")
                    return Response({"error": "Failed to send password reset email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetView(views.APIView):
    """
    Reset a user's password.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Reset Password", request_body=PasswordResetSerializer)
    def post(self, request, uidb64=None, token=None):
        """
        Handle password reset.
        """
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Decode the user's ID from the base64-encoded UID
            try:
                uid = urlsafe_base64_decode(uidb64).decode()
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            # Check if the token is valid
            if user is not None and default_token_generator.check_token(user, token):
                # Set the new password
                new_password = serializer.validated_data['new_password']
                user.set_password(new_password)
                user.save()

                return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid token or user ID."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def logout_view(request):
    """
    View to log out the user by blacklisting the refresh token and clearing session cookies.
    """
    # Get the refresh token from the cookies
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({"error": "No refresh token provided"}, status=400)

    try:
        # Blacklist the refresh token
        token = RefreshToken(refresh_token)
        token.blacklist()

        # Clear the cookies 
        response = Response({"message": "Logged out successfully"}, status=200)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.delete_cookie('csrftoken')  
        return response

    except Exception as e:
        return Response({"error": str(e)}, status=400)
    

class UserListView(ListAPIView):
    """
    List users based on the role of the requester.
    Superusers and Admins can see all users.
    Technicians cannot access this view.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_role == User.UseRole.ADMIN:
            # Superusers and Admins can see all users
            return User.objects.all().order_by('id')
        else:
            # Technicians cannot see any users
            raise PermissionDenied(detail="You do not have permission to view this resource.")
        
        

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])  # Ensure the user is authenticated first
def total_users_view(request):
    """
    Get the total number of users.
    Only accessible by Admins and Superusers.
    """
    user = request.user

    # Check if the user is a superuser or an admin
    if user.is_superuser or user.user_role == User.UseRole.ADMIN:
        total_users = User.objects.count()
        return Response({"total_users": total_users})
    else:
        # If the user is not a superuser or admin, raise PermissionDenied
        raise PermissionDenied(detail="You do not have permission to view this resource.")


class AuditLogView(ListAPIView):
    """
    API view to list audit logs.
    Only accessible by Admins and Superadmins.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]  # Only authenticated users can access

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_role == User.UseRole.ADMIN:
            # Admins and Superadmins can view all audit logs
            return AuditLog.objects.all().order_by('-timestamp')
        else:
            # Technicians cannot access audit logs, raise PermissionDenied
            raise PermissionDenied(detail="You do not have permission to view audit logs.")