from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import MaintenanceSchedule
from notification.models import Notification
from django.db import transaction
from datetime import timedelta
import logging
from .tasks import send_maintenance_reminder  # Import the task

logger = logging.getLogger(__name__)

@receiver(post_save, sender=MaintenanceSchedule)
def send_maintenance_notification(sender, instance, created, **kwargs):
    with transaction.atomic():
        if created:
            message = f"New maintenance schedule created: {instance.title}"
        else:
            message = f"Maintenance schedule updated: {instance.title}"

        notification = Notification.objects.create(
            user=instance.technician,
            message=message,
            link=reverse('maintenance-schedule-detail', kwargs={'pk': instance.pk})
        )

        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        try:
            channel_layer = get_channel_layer()
            group_name = f"notification_user_{instance.technician.id}"
            event = {
                "type": "notification.message",
                "message": message,
                "link": notification.link
            }
            async_to_sync(channel_layer.group_send)(group_name, event)
        except Exception as e:
            # Log the error and continue
            logger.error(f"Failed to send real-time notification: {e}")



@receiver(post_save, sender=MaintenanceSchedule)
def schedule_reminder_task(sender, instance, created, **kwargs):
    """
    Dynamically schedule reminder task when a maintenance schedule is created or updated.
    """
    # Get the next occurrence of the maintenance schedule
    occurrences = instance.get_next_occurrences()
    
    if not occurrences:
        return  # No occurrences to schedule

    next_occurrence = occurrences[0]

    # Schedule the reminder task 24 hours before the next occurrence
    reminder_time = next_occurrence - timedelta(hours=24)

    # Use apply_async to schedule the task dynamically
    send_maintenance_reminder.apply_async(
        args=[instance.id, next_occurrence],  # Pass schedule id and occurrence time
        eta=reminder_time  # Set the ETA for 24 hours before the occurrence
    )