from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from firebase_admin import auth as firebase_auth
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class UserManager:
    @staticmethod
    def handle_user(decoded_token):
        is_anonymous = decoded_token.get('firebase', {}).get('sign_in_provider') == 'anonymous'
        
        if is_anonymous:
            logger.info('Anonymous user login attempt')
            return AnonymousUser(), None  # Handle anonymous users if you need to allow them without creation

        email = decoded_token.get('email')
        if not email:
            logger.error('Invalid Firebase token: No email found')
            return None, 'Invalid Firebase token'
        
        first_name = decoded_token.get('name', '').split()[0] if 'name' in decoded_token else ''
        last_name = ' '.join(decoded_token.get('name', '').split()[1:]) if 'name' in decoded_token and len(decoded_token.get('name', '').split()) > 1 else ''
        
        user, created = User.objects.get_or_create(email=email, defaults={
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': decoded_token.get('phone_number', ''),
        })

        if not created:
            # Update the user profile if necessary
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = decoded_token.get('phone_number', '')
            user.save()
            logger.info(f'Updated existing user: {email}')
        else:
            logger.info(f'Created new user: {email}')

        return user, None
