
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status, views, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from django.template import TemplateDoesNotExist
from django.conf import settings
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
import firebase_admin
from firebase_admin import auth as firebase_auth
from accounts.authentication.firebase_authentication import FirebaseAuthentication
from .utils import UserManager
from .serializers import *


from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode





User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegistrationView(views.APIView):
    """
    API endpoint for registering a new user.
    Superusers can create Admins and Users.
    Admins can only create regular Users.
    """
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can create accounts

    @swagger_auto_schema(
        operation_summary="Register a new user",
        request_body=UserRegistrationSerializer,
        responses={201: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        # Pass the request to the serializer for context
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        
        # Validate the serializer
        if serializer.is_valid():
            try:
                # Save the user and send the account creation email
                user = serializer.save()

                # Token generation for the new user
                token = RefreshToken.for_user(user)
                
                # Log the success and proceed with sending email
                logger.info(f"User created successfully: {user.email}")

                # Prepare the response with user details and tokens
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(token),
                    'access': str(token.access_token)
                }, status=status.HTTP_201_CREATED)

            except TemplateDoesNotExist as e:
                logger.error(f"Template not found: {e}")
                return Response({"error": "Email template not found."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"Error during user creation: {e}")
                return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
   
class GoogleAuthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Authenticate via Google OAuth2",
        request_body=GoogleAuthSerializer,
        responses={200: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            id_token = serializer.validated_data.get('id_token')
            firebase_auth = FirebaseAuthentication()
            decoded_token, error = firebase_auth.authenticate_token(id_token)

            if not decoded_token:
                logger.error(f'Authentication failed: {error}')
                return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)

            user, error = UserManager.handle_user(decoded_token)
            if user:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                logger.info(f'User authenticated: {user.email}')
                return Response({
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(access)
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f'User management error: {error}')
                return Response({'detail': error}, status=status.HTTP_400_BAD_REQUEST)
        logger.error(f'Invalid data: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    API endpoint for obtaining JWT tokens with custom claims.
    Generates access and refresh JWT tokens for authenticated users.
    """
    serializer_class = CustomTokenObtainPairSerializer

    @swagger_auto_schema(
        operation_summary="Obtain JWT tokens",
        responses={200: "Tokens obtained", 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    

class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the details of a user.
    Admins and Superusers can update user profiles, but they cannot update passwords.
    Regular users cannot edit their profile.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Allow Admins and Superusers to edit any user profile, but regular users cannot edit their own profile.
        """
        obj = super().get_object()
        if self.request.user.user_type == 3:  # Regular user
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
        serializer = PasswordResetSerializer(data=request.data)
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
            user = User.objects.filter(email=email).first()
            
            if user:
                # Generate a one-time-use token and a UID
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                # Construct the password reset URL
                reset_url = request.build_absolute_uri(reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token}))

                # Send email
                subject = 'Password Reset Request'
                message = render_to_string('password_reset_email.html', {
                    'user': user,
                    'reset_url': reset_url,
                })
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

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
    
    
class UserListView(ListAPIView):
    """
    List users based on the role of the requester.
    Superusers can see all users.
    Admins can only see regular users.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
             return User.objects.all().order_by('id')  # Superusers can see all users
        elif user.user_type == 2:  # Admin
            return User.objects.filter(user_type=3).order_by('id')  # Admins can only see regular users
        else:
            return User.objects.none()  # Regular users can't access the user list


@api_view(['GET'])
def total_users_view(request):
    """
    Get the total number of users.
    """
    total_users = User.objects.count()
    return Response({"total_users": total_users})

