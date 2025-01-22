import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token):
    """
    Given a verified token, return the corresponding user instance or None.
    """
    try:
        UntypedToken(token)  # This will raise an error if the token is invalid
    except (InvalidToken, TokenError, jwt.DecodeError):
        return None

    # Decode does not do the same checks as UntypedToken, but we can still get user_id:
    decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    user_id = decoded_data.get("user_id")
    if not user_id:
        return None

    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None

class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom Channels middleware that takes a JWT from the query string (e.g. ?token=<JWT>)
    and authenticates the user.
    """

    async def __call__(self, scope, receive, send):
        query_dict = parse_qs(scope["query_string"].decode())
        token = query_dict.get("token", [None])[0]

        # Very naive parsing. In production, use proper URL parsing.
        if 'token=' in query_dict:
            token = query_dict.split('token=')[-1]

        if token:
            user = await get_user_from_token(token)
            if user:
                scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)

def JWTAuthMiddlewareStack(inner):
    """
    Returns a JWTAuthMiddleware stacked on top of the default Django Auth.
    """
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
