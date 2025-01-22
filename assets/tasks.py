from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import MaintenanceSchedule
from celery.utils.log import get_task_logger
from notification.models import Notification


logger = get_task_logger(__name__)


@shared_task
@shared_task
def send_maintenance_reminder(schedule_id, occurrence):
    """
    Task to send a single maintenance reminder.
    """
    try:
        schedule = MaintenanceSchedule.objects.select_related('technician', 'asset').get(id=schedule_id)
        technician = schedule.technician
        
        if technician:
            # Prepare email content
            subject = f"Reminder: {schedule.title}"
            context = {
                'technician': technician,
                'schedule': schedule,
                'occurrence': occurrence,
            }
            message = render_to_string('assets/maintenance_reminder.html', context)

            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body='',  # plain text part (optional)
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[technician.email],
            )
            email.attach_alternative(message, "text/html")
            email.send()

        # Prepare notification message
        if schedule.is_general:
            asset_name = "General Maintenance"
        elif schedule.asset:
            asset_name = schedule.asset.name
        else:
            asset_name = "Unknown Asset"

        # Create in-app notification
        Notification.objects.create(
            user=technician,
            message=f"You have a scheduled maintenance for {asset_name} on {occurrence.strftime('%Y-%m-%d %H:%M')}",
            link=f'/maintenance-schedules/{schedule.id}/'
        )

        # Update last_notification
        schedule.last_notification = timezone.now()
        schedule.save()

        logger.info(f"Reminder sent successfully for schedule {schedule.id}")

    except MaintenanceSchedule.DoesNotExist:
        logger.error(f"MaintenanceSchedule with id {schedule_id} does not exist.")
    except Exception as e:
        logger.error(f"Failed to send reminder for schedule {schedule_id}: {e}")
