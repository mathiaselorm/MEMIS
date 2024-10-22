from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

class CookieJWTAuthentication(BaseAuthentication):
    """
    Custom authentication class that checks the JWT token in the HttpOnly cookie.
    """
    def authenticate(self, request):
        # Check if the access token exists in cookies
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            raise AuthenticationFailed('Authentication failed: No JWT token found in cookies.')
        
        # Try to validate the token
        try:
            validated_token = AccessToken(access_token)
        except AccessToken.DoesNotExist:
            raise AuthenticationFailed("Authentication failed: Invalid JWT token.")
        except AccessToken.ExpiredSignatureError:
            raise AuthenticationFailed("Authentication failed: Token has expired.")
        except Exception as e:
            raise AuthenticationFailed(f"Authentication failed: {str(e)}.")
        
        # Retrieve the user associated with the token
        user = self.get_user_from_token(validated_token)
        
        if user is None:
            raise AuthenticationFailed("Authentication failed: User not found or inactive.")
        
        return (user, None)

    def get_user_from_token(self, token):
        """
        Retrieves the user from the token's payload.
        """
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_id = token.get('user_id')
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
