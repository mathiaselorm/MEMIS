# tasks.py

from celery import shared_task
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import MaintenanceSchedule, Notification

@shared_task
def send_maintenance_reminders():
    now = datetime.now()
    schedules = MaintenanceSchedule.objects.filter(is_active=True)

    for schedule in schedules:
        occurrences = schedule.get_next_occurrences()
        for occurrence in occurrences:
            time_until = occurrence - now
            hours_until = time_until.total_seconds() / 3600

            if 0 <= hours_until <= 24 and (not schedule.last_notification or schedule.last_notification < now - timedelta(hours=24)):
                technician = schedule.technician
                if technician:
                    occurrence_local = occurrence

                    # Prepare email content
                    subject = f"Reminder: {schedule.title}"
                    context = {
                        'technician': technician,
                        'schedule': schedule,
                        'occurrence': occurrence_local,
                    }
                    message = render_to_string('assets/maintenance_reminder.html', context)
                    send_mail(
                        subject=subject,
                        message='',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[technician.email],
                        html_message=message,
                    )

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
                        message=f"You have a scheduled maintenance for {asset_name} on {occurrence_local.strftime('%Y-%m-%d %H:%M')}",
                        link=f'/maintenance-schedules/{schedule.id}/'
                    )

                    # Update last_notification
                    schedule.last_notification = now
                    schedule.save()
