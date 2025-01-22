
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Notification

@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, created, **kwargs):
    """
    Whenever a new Notification is saved (or updated),
    send a message to the user's group via Channels.
    """

    # user_{id} group
    user_id = instance.user.id
    group_name = f"user_{user_id}"

    # Construct the event
    event = {
        "type": "notification_message",
        "title": "New Notification",  # or instance.title if you have a title field
        "message": instance.message,
        "link": instance.link or "",
    }

    # Get channel layer and send the event
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(group_name, event)
