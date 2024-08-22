import logging
from rest_framework import authentication, exceptions
from firebase_admin import auth

logger = logging.getLogger(__name__)

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            logger.warning('No Authorization header found')
            return None, None

        try:
            token = auth_header.split(' ')[1]
            decoded_token = auth.verify_id_token(token)
            logger.info('Firebase token verified successfully')
            return decoded_token, None
        except (IndexError, ValueError):
            logger.error('Invalid token format')
            return None, 'Invalid token format'
        except auth.InvalidIdTokenError:
            logger.error('Invalid Firebase token')
            return None, 'Invalid Firebase token'
        except auth.ExpiredIdTokenError:
            logger.error('Expired Firebase token')
            return None, 'Expired Firebase token'
        except auth.RevokedIdTokenError:
            logger.error('Revoked Firebase token')
            return None, 'Revoked Firebase token'
        except Exception as e:
            logger.error(f'Firebase authentication error: {str(e)}')
            return None, str(e)

    def authenticate_token(self, token):
        try:
            decoded_token = auth.verify_id_token(token)
            logger.info('Firebase token verified successfully')
            return decoded_token, None
        except (IndexError, ValueError):
            logger.error('Invalid token format')
            return None, 'Invalid token format'
        except auth.InvalidIdTokenError:
            logger.error('Invalid Firebase token')
            return None, 'Invalid Firebase token'
        except auth.ExpiredIdTokenError:
            logger.error('Expired Firebase token')
            return None, 'Expired Firebase token'
        except auth.RevokedIdTokenError:
            logger.error('Revoked Firebase token')
            return None, 'Revoked Firebase token'
        except Exception as e:
            logger.error(f'Firebase authentication error: {str(e)}')
            return None, str(e)
