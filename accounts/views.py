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




# # Secure cookie setting for production
# secure_cookie = not settings.DEBUG  # Set secure=True in production

# # Token lifetimes (extracted from SimpleJWT settings)
# access_token_lifetime = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
# refresh_token_lifetime = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()


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
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'last_name', 'email', 'password', 'user_role'],  # This should be a list, not a boolean
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='User\'s first name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='User\'s last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User\'s email address'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='User\'s phone number (optional)', nullable=True),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='User\'s password (must meet minimum strength requirements)'),
                'user_role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['Superadmin', 'Admin', 'Technician'],
                    description='Role to be assigned to the user. Choose between Superadmin, Admin, or Technician.'
                )
            },
            example={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone_number": "+1234567890",
                "password": "Password123!",
                "user_role": "Admin"
            }
        ),
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
        Admins and Superadmins can assign or change a user's role. The available roles are:
        - Superadmin
        - Admin
        - Technician

        Admins cannot assign the Superadmin role. Technicians are not allowed to assign roles.
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['first_name', 'new_role'],
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="First name of the user whose role is to be changed"),
                'new_role': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['Superadmin', 'Admin', 'Technician'],
                    description="The new role to assign to the user. Options: 'Superadmin', 'Admin', 'Technician'"
                )
            },
            example={
                "first_name": "john_doe",
                "new_role": "Admin"
            }
        ),
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
                        "first_name": ["User with this first name does not exist."],
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
        tags=["Authentication"]
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
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    

#     @swagger_auto_schema(
#         operation_summary="Obtain JWT access and refresh tokens",
#         operation_description="""
#         Authenticated users can obtain JWT access and refresh tokens. 
#         The tokens are set in HttpOnly cookies.
#         """,
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             required=["email", "password"],
#             properties={
#                 "email": openapi.Schema(
#                     type=openapi.TYPE_STRING,
#                     description="User's email address",
#                     example="user@example.com"
#                 ),
#                 "password": openapi.Schema(
#                     type=openapi.TYPE_STRING,
#                     description="User's password",
#                     example="password123"
#                 ),
#             },
#             example={
#                 "email": "user@example.com",
#                 "password": "password123"
#             }
#         ),
#         responses={
#             200: openapi.Response(
#                 description="Tokens obtained successfully and set in HttpOnly cookies.",
#                 examples={
#                     "application/json": {
#                         "message": "Access token and refresh token set in HttpOnly cookie."
#                     }
#                 }
#             ),
#             400: openapi.Response(
#                 description="Bad Request - Failed to generate tokens.",
#                 examples={
#                     "application/json": {
#                         "error": "Failed to generate tokens."
#                     }
#                 }
#             ),
#             401: openapi.Response(
#                 description="Unauthorized - Invalid credentials.",
#                 examples={
#                     "application/json": {
#                         "error": "Invalid credentials."
#                     }
#                 }
#             ),
#         },
#         tags=["Authentication"]
#     )
#     def post(self, request, *args, **kwargs):
#         # Call the default TokenObtainPairView to generate tokens
#         response = super().post(request, *args, **kwargs)

#         if response.status_code == 200:
#             # Extract the tokens from the response
#             tokens = response.data
#             access_token = tokens.get('access')
#             refresh_token = tokens.get('refresh')
#             csrf_token = get_token(request)

#             # Ensure the tokens exist
#             if not access_token or not refresh_token:
#                 return Response({"error": "Failed to generate tokens."}, status=status.HTTP_400_BAD_REQUEST)
            
#             # response = Response({"message": "Access token and refresh token set in HttpOnly cookie."}, status=status.HTTP_200_OK)
            
#             # Set access token in HttpOnly cookie
#             response.set_cookie(
#                 key='access_token',
#                 value=access_token,
#                 httponly=True,
#                 secure=secure_cookie,  # Ensure secure cookie in production
#                 samesite='Lax' if settings.DEBUG else 'None',  # SameSite attribute
#                 max_age=access_token_lifetime,  # Expiration matches access token lifetime
#             )

#             # Set refresh token in HttpOnly cookie
#             response.set_cookie(
#                 key='refresh_token',
#                 value=refresh_token,
#                 httponly=True,
#                 secure=secure_cookie,  # Ensure secure cookie in production
#                 samesite='Lax' if settings.DEBUG else 'None',  # SameSite attribute
#                 max_age=refresh_token_lifetime,  # Expiration matches refresh token lifetime
#             )

#             response.set_cookie(
#                 key='csrftoken',
#                 value=csrf_token,
#                 httponly=False,  # Needs to be readable by the frontend
#                 secure=secure_cookie,  # Set secure=True in production
#                 samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
#                 max_age=access_token_lifetime,  # Set cookie expiration to match access token
#             )
            
#             return response

#         # If the request fails (e.g., wrong credentials)
#         return Response({"error": "Invalid credentials."}, status=response.status_code)
    

# class CustomTokenRefreshView(APIView):
#     """
#     API endpoint for refreshing JWT access tokens.
#     Uses the refresh token stored in cookies to generate a new access token.
#     """

#     @swagger_auto_schema(
#         operation_summary="Refresh JWT access token",
#         operation_description="""
#         This API endpoint allows users to refresh their JWT access token using the refresh token stored in HttpOnly cookies.
#         The response will include:
        
#         - A new access token (set in an HttpOnly cookie).
#         - A new CSRF token (sent in a readable cookie for frontend protection).
        
#         No request body is required as the refresh token is retrieved from the cookies.
#         """,
#         request_body=None,  # No request body required
#         responses={
#             200: openapi.Response(
#                 description="Access token refreshed successfully. Tokens are set in HttpOnly cookies.",
#                 examples={
#                     "application/json": {
#                         "message": "New access token set in HttpOnly cookie."
#                     }
#                 },
#                 headers={
#                     "Set-Cookie": openapi.Schema(
#                         description="JWT Access token and CSRF token set in cookies.",
#                         type="string"
#                     )
#                 }
#             ),
#             400: openapi.Response(
#                 description="Refresh token not found or invalid.",
#                 examples={
#                     "application/json": {
#                         "error": "Refresh token not found."
#                     }
#                 }
#             ),
#             401: openapi.Response(
#                 description="Unauthorized. The refresh token may have expired or been blacklisted.",
#                 examples={
#                     "application/json": {
#                         "detail": "Token is invalid or expired."
#                     }
#                 }
#             ),
#         },
#         tags=['Authentication'],
#     )
#     def post(self, request, *args, **kwargs):
#         # Get the refresh token from the cookies
#         refresh_token = request.COOKIES.get('refresh_token')
#         secure_cookie = not settings.DEBUG  # Set secure=True in production

#         if not refresh_token:
#             return Response({"error": "Refresh token not found"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Validate the refresh token
#             refresh = RefreshToken(refresh_token)

#             # Extract custom claims from refresh token payload, excluding standard claims
#             custom_claims = {key: value for key, value in refresh.payload.items() 
#                              if key not in ['token_type', 'exp', 'iat', 'jti']}

#             # Generate a new access token
#             new_access_token = refresh.access_token

#             # Add custom claims to the new access token
#             for key, value in custom_claims.items():
#                 new_access_token[key] = value

#             # Handle refresh token rotation if enabled
#             if api_settings.ROTATE_REFRESH_TOKENS:
#                 # Generate a new refresh token
#                 new_refresh_token = RefreshToken()

#                 # Add custom claims to the new refresh token
#                 for key, value in custom_claims.items():
#                     new_refresh_token[key] = value

#                 # Set the new refresh token in HttpOnly cookie
#                 response = Response({"message": "New access token and refresh token set in HttpOnly cookie."}, status=status.HTTP_200_OK)
#                 response.set_cookie(
#                     key='refresh_token',
#                     value=str(new_refresh_token),  # Use the new refresh token
#                     httponly=True,
#                     secure=secure_cookie,  # Set secure=True in production
#                     samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
#                     max_age=refresh_token_lifetime,  # Set cookie expiration to match refresh token
#                 )

#                 # Blacklist the old refresh token after the new one is securely sent
#                 refresh.blacklist()
#             else:
#                 response = Response({"message": "New access token set in HttpOnly cookie."}, status=status.HTTP_200_OK)

#             # Set the new access token in HttpOnly cookie
#             response.set_cookie(
#                 key='access_token',
#                 value=str(new_access_token),
#                 httponly=True,
#                 secure=secure_cookie,  # Set secure=True in production
#                 samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
#                 max_age=access_token_lifetime,  # Set cookie expiration to match access token
#             )

#             # Generate and set a new CSRF token
#             csrf_token = get_token(request)
#             response.set_cookie(
#                 key='csrftoken',
#                 value=csrf_token,
#                 httponly=False,  # Needs to be readable by the frontend
#                 secure=secure_cookie,  # Set secure=True in production
#                 samesite='Lax' if settings.DEBUG else 'None',  # Set SameSite=Lax in dev, None in production
#                 max_age=access_token_lifetime,  # Set cookie expiration to match access token
#             )

#             # Return the new access token for debugging in development
#             if settings.DEBUG:
#                 response.data['access_token'] = str(new_access_token)

#             return response

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
        

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the details of a user.
    Admins and Superusers can update user profiles, but they cannot update passwords.
    Regular users cannot edit their own profile.
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
    
    
    
class PasswordChangeView(views.APIView):
    """
    API endpoint for changing the user's password.
    Allows authenticated users (regular users, admins, and superadmins) to change their own password.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Change User Password",
        operation_description="Allows authenticated users to change their password by providing the old password and the new password.",
        request_body=PasswordChangeSerializer,
        responses={
            200: openapi.Response(
                description="Password updated successfully.",
                examples={
                    "application/json": {
                        "message": "Password updated successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Validation Error",
                examples={
                    "application/json": {
                        "old_password": ["The old password is incorrect."],
                        "new_password": ["The password must be at least 8 characters long."]
                    }
                }
            )
        },
        tags=["Password Management"]
    )
    def post(self, request):
        """
        Handle password change for authenticated users.
        """
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user  # Get the currently authenticated user
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)  # Update the user's password
            user.save()
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(views.APIView):
    """
    API endpoint to request a password reset via email.
    Accepts user's email and frontend URL, sends a reset link if the email is valid.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Request Password Reset",
        operation_description="Allows users to request a password reset by providing their email and frontend URL for redirect. A reset link will be sent to the provided email if valid.",
        request_body=PasswordResetRequestSerializer,
        responses={
            200: openapi.Response(
                description="Password reset email sent successfully.",
                examples={
                    "application/json": {
                        "message": "Password reset email sent."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Invalid email or other validation errors.",
                examples={
                    "application/json": {
                        "email": ["No user is associated with this email address."]
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error - Failed to send email.",
                examples={
                    "application/json": {
                        "error": "Failed to send password reset email."
                    }
                }
            )
        },
        tags=["Password Management"]
    )
    def post(self, request):
        """
        Handle password reset requests. Send an email with a password reset link if the provided email is valid.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            frontend_url = serializer.validated_data['frontend_url']  # Get the frontend URL from the request
            
            user = User.objects.filter(email=email).first()
            if user:
                # Generate a one-time-use token and UID for password reset
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Construct the password reset URL using the frontend URL
                reset_url = f"{frontend_url}/password-reset/{uid}/{token}/"

                try:
                    # Send the password reset email (this could be a background task)
                    send_password_reset_email(user.id, reset_url)
                except Exception as e:
                    logger.error(f"Failed to send email: {e}")
                    return Response({"error": "Failed to send password reset email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)

        # If serializer validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetView(views.APIView):
    """
    Reset a user's password.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Reset User Password",
        operation_description="Allows users to reset their password by providing a valid token and setting a new password.",
        request_body=PasswordResetSerializer,
        responses={
            200: openapi.Response(
                description="Password has been reset successfully.",
                examples={
                    "application/json": {
                        "message": "Password has been reset successfully."
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Invalid token or user ID.",
                examples={
                    "application/json": {
                        "message": "Invalid token or user ID."
                    }
                }
            ),
        },
        tags=["Password Management"]
    )
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
 

@swagger_auto_schema(
    method='post',
    operation_summary="Log Out User",
    operation_description="""
    Logs out the user by blacklisting the refresh token and clearing the session cookies.
    """,
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
        """
        Handle GET requests to list users based on their role.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.user_role == User.UseRole.ADMIN:
            # Superusers and Admins can see all users
            return User.objects.all().order_by('id')
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