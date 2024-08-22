import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserProfile
from django.db.utils import IntegrityError

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create or update a user profile whenever a user instance is saved.
    """
    try:
        if created:
            # Create a new user profile if this is a new user
            UserProfile.objects.get_or_create(user=instance)
            logger.info(f"New user profile created for {instance.email}")
        else:
            # Attempt to update the user profile if it exists, or create it if not
            profile, created = UserProfile.objects.update_or_create(
                user=instance,
                defaults={
                    # Placeholder for fields that might be updated from user instance
                    # For example:
                    # 'some_field': instance.related_field,
                }
            )
            if created:
                logger.info(f"User profile newly created for {instance.email}")
            else:
                logger.info(f"User profile updated for {instance.email}")

    except IntegrityError as e:
        logger.error(f"Failed to create or update user profile for {instance.email}: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while creating or updating the user profile for {instance.email}: {str(e)}")
