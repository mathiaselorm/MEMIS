import logging
from django.core.mail import EmailMultiAlternatives
from background_task import background
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

# Initialize logging
logger = logging.getLogger(__name__)

# Get the user model
User = get_user_model()

@background(schedule=0)  # Task runs immediately
def send_welcome_email(user_email, user_pk, reset_url):
    """
    Sends a welcome email with a link to set the user's password.
    """
    try:
        # Retrieve the user instance by primary key
        user = User.objects.get(pk=user_pk)

        # Render the email template with context
        subject = 'Set Your Password'
        context = {
            'user': user,
            'reset_url': reset_url,
        }

        # Generate plain text and HTML content
        text_content = f"Hello {user.first_name},\nPlease click the link below to set your password: {reset_url}"
        html_content = render_to_string('accounts/account_creation_email.html', context)

        # Create email using EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # Plain text content
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )

        # Attach HTML version of the email
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        # Log success
        logger.info(f"Welcome email sent to {user_email}.")

    except User.DoesNotExist:
        # Log error if user not found
        logger.error(f"User with pk {user_pk} does not exist. Welcome email not sent.")
    except Exception as e:
        # Log any other exceptions
        logger.error(f"Error sending welcome email to {user_email}: {e}")


@background(schedule=5)  # Task runs 5 seconds after it's called
def send_password_reset_email(user_id, reset_url):
    """
    Sends a password reset email to the user.
    """
    try:
        # Retrieve the user instance
        user = User.objects.get(pk=user_id)

        # Render the email template
        subject = 'Password Reset Request'
        context = {
            'user': user,
            'reset_url': reset_url,
        }

        # Generate plain text and HTML content
        text_content = f"Hello {user.first_name},\nYou requested a password reset. Click the link below to reset your password: {reset_url}"
        html_content = render_to_string('accounts/password_reset_email.html', context)

        # Create email using EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,  # Plain text content
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]  # Sending to the user's email
        )

        # Attach HTML version of the email
        email.attach_alternative(html_content, "text/html")

        # Send email
        email.send()

        # Log success
        logger.info(f"Password reset email sent to {user.email}.")

    except User.DoesNotExist:
        # Log error if user not found
        logger.error(f"User with id {user_id} does not exist. Password reset email not sent.")
    except Exception as e:
        # Log any other exceptions
        logger.error(f"Error sending password reset email to {user.email if user else 'Unknown'}: {e}")
