from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import MaintenanceSchedule
from django.utils.html import strip_tags
from celery.utils.log import get_task_logger
from notification.models import Notification


logger = get_task_logger(__name__)


@shared_task
def send_maintenance_reminder(schedule_id, occurrence):
    """
    Send a maintenance reminder email and notification.
    """
    try:
        schedule = MaintenanceSchedule.objects.select_related('technician', 'equipment').get(id=schedule_id)
    except MaintenanceSchedule.DoesNotExist:
        logger.error(f"Failed to send reminder: MaintenanceSchedule with ID {schedule_id} does not exist.")
        return

    technician = schedule.technician
    if not technician:
        logger.error(f"No technician assigned for schedule {schedule_id}.")
        return

    try:
        # Prepare email content
        subject = f"Reminder: {schedule.title}"
        context = {
            'technician': technician,
            'schedule': schedule,
            'occurrence': occurrence,
            'current_year': timezone.now().year,  # Ensure you have the current year
            'equipment_name': schedule.equipment.name if schedule.equipment else "For All Equipment",

        }
        html_content = render_to_string('equipment/maintenance_reminder.html', context)
        text_content = strip_tags(html_content)

        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[technician.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        logger.info(f"Reminder email sent for schedule {schedule_id} to {technician.email}")
    except Exception as e:
        logger.error(f"Failed to send reminder email for schedule {schedule_id}: {e}")

    # Create in-app notification
    try:
        Notification.objects.create(
            user=technician,
            message=f"Reminder: {schedule.title} scheduled for {occurrence.strftime('%Y-%m-%d %H:%M')}.",
            link=f'/maintenance-schedules/{schedule.id}/'
        )
        logger.info(f"Notification created for schedule {schedule_id}.")
    except Exception as e:
        logger.error(f"Failed to create notification for schedule {schedule_id}: {e}")