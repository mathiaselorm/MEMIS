from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from .models import Item
from notification.models import Notification
from accounts.models import CustomUser
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Item)
def notify_low_or_out_of_stock(sender, instance, created, **kwargs):
    """
    Create a notification if the item is low/out of stock.
    """
    # Determine if it's low stock or out of stock
    if instance.quantity == 0:
        status_msg = "Out of Stock"
    elif instance.quantity <= 5:
        status_msg = "Low Stock"
    else:
        return  # If it's neither out nor low, do nothing

    # Build the notification message
    message = f"Inventory Alert: '{instance.name}' ({instance.item_code}) is {status_msg}."

    # Fetch all ADMIN or SUPERADMIN users
    admin_users = CustomUser.objects.filter(
        user_role__in=[
            CustomUser.UserRole.ADMIN,
            CustomUser.UserRole.SUPERADMIN
        ]
    )

    # Create a notification & optionally broadcast via WebSockets
    for admin_user in admin_users:
        notification = Notification.objects.create(
            user=admin_user,
            message=message,
            link=reverse('item-detail', kwargs={'pk': instance.pk}),  # adapt your URL name
        )
        try:
            channel_layer = get_channel_layer()
            group_name = f"notification_user_{admin_user.id}"
            event = {
                "type": "notification.message",  # Must match the consumer's method name
                "message": message,
                "link": notification.link,
            }
            async_to_sync(channel_layer.group_send)(group_name, event)
        except Exception as e:
            logger.error(f"Failed to send real-time notification: {e}")
