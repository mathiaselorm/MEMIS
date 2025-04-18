import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.signals import reset_password_token_created

from .tasks import send_password_reset_email

logger = logging.getLogger(__name__)

User = get_user_model()

@receiver(reset_password_token_created)
def password_reset_token_created_handler(sender, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens by sending an email via Celery.
    """
    try:
        # Determine the context
        created_via = kwargs.get('created_via', 'password_reset')

        # Select email template and subject based on context
        if created_via == 'registration':
            email_template = 'accounts/account_creation_email.html'
            subject = _('Welcome to MEMIS - Set Your Password')
        else:
            email_template = 'accounts/password_reset_email.html'
            subject = _('Password Reset Request')
            
        # current_site = Site.objects.get_current()
        # Build the reset URL
        frontend_url = settings.FRONTEND_URL
        reset_url = f"{frontend_url}/reset-password?token={reset_password_token.key}"
        
        logger.debug(f"Reset URL generated: {reset_url} for user {reset_password_token.user.email}")

        send_password_reset_email.delay(
            user_id=reset_password_token.user.id,
            subject=subject,
            email_template=email_template,
            context={
                'user_name': reset_password_token.user.get_full_name(),
                'reset_url': reset_url,
            }
        )

        logger.info(f"Password reset email sent to {reset_password_token.user.email} for {created_via}.")

    except Exception as e:
        logger.error(f"Error sending password reset email to {reset_password_token.user.email}: {e}")
        
