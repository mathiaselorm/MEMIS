
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status, views, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken
import firebase_admin
from firebase_admin import auth as firebase_auth
from accounts.authentication.firebase_authentication import FirebaseAuthentication
from .utils import UserManager
from .serializers import *





User = get_user_model()
logger = logging.getLogger(__name__)

class UserRegistrationView(views.APIView):
    """
    API endpoint for registering a new user.
    Allows any user to register to the system using an email and password.
    """
    permission_classes = [permissions.AllowAny]
    @swagger_auto_schema(
        operation_summary="Register a new user",
        request_body=UserRegistrationSerializer,
        responses={201: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(token),
                'access': str(token.access_token)
            }, status=status.HTTP_201_CREATED)
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
    

class AppleAuthView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Authenticate via Apple OAuth2",
        request_body=AppleAuthSerializer,
        responses={200: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request, *args, **kwargs):
        serializer = AppleAuthSerializer(data=request.data)
        if serializer.is_valid():
            id_token = serializer.validated_data.get('identity_token')
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
    Retrieve or update a user instance.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_summary="Retrieve User Details")
    def get(self, request, *args, **kwargs):
        """
        Retrieve the details of a user.
        """
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update User Details")
    def put(self, request, *args, **kwargs):
        """
        Update the details of a user.
        """
        return self.update(request, *args, **kwargs)
    
    @swagger_auto_schema(operation_summary="Partially Update User Details")
    def patch(self, request, *args, **kwargs):
        """
        Partially update the details of a user.
        """
        kwargs['partial'] = True
        return self.put(request, *args, **kwargs)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a user's profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Override the default get_object method to return the profile
        of the current user.
        """
        return self.request.user.profile

    @swagger_auto_schema(operation_summary="Get User Profile")
    def get(self, request, *args, **kwargs):
        """
        Retrieve the user's profile.
        """
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Update User Profile")
    def put(self, request, *args, **kwargs):
        """
        Update the user's profile.
        """
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Partially Update User Profile")
    def patch(self, request, *args, **kwargs):
        """
        Partially update the user's profile.
        """
        return super().update(request, *args, **kwargs)

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
            # Here you would implement your logic to send a reset email
            return Response({"message": "Password reset email sent."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetView(views.APIView):
    """
    Reset a user's password.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="Reset Password", request_body=PasswordResetSerializer)
    def post(self, request):
        """
        Handle password reset.
        """
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Implement password reset logic here, including token verification
            return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(ListAPIView):
    """
    List all users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  # Adjust as necessary to IsAdminUser

@api_view(['GET'])
def total_users_view(request):
    """
    Get the total number of users.
    """
    total_users = User.objects.count()
    return Response({"total_users": total_users})



"""
    class LoginView(views.APIView):
   
    User login view.
   
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="User Login",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "refresh": "refresh token",
                        "access": "access token"
                    }
                }
            ),
            401: "Invalid credentials"
        }
    )
    def post(self, request):
      
        Handle user login and return JWT tokens.
       
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(username=serializer.validated_data['email'], password=serializer.validated_data['password'])
            if user:
                refresh = RefreshToken.for_user(user)
                logger.info(f"Login successful for user {user.email}")
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Login failed for email: {serializer.validated_data['email']}")
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.error(f"Login attempt with invalid data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """