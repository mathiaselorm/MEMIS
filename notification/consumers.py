import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class NotificationConsumer(AsyncWebsocketConsumer):
    """
    A consumer that handles real-time notifications for an authenticated user
    using a custom JWTAuthMiddlewareStack.
    """

    async def connect(self):
        self.user = self.scope.get("user", None)

        if not self.user or isinstance(self.user, AnonymousUser):
            logger.debug("Closing WebSocket because user is not authenticated.")
            await self.close()
            return

        self.group_name = f"notification_user_{self.user.id}"
        logger.debug(f"User {self.user.email} connecting to group {self.group_name}")

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            logger.debug(f"User {self.user.email} disconnecting from {self.group_name} with code {close_code}")
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def notification_message(self, event):
        """
        This method is called whenever a message is sent to this user's group.
        """
        logger.debug(f"Sending message to {self.user.email}: {event}")
        await self.send(text_data=json.dumps({
            "title": event.get("title", ""),
            "message": event.get("message", ""),
            "link": event.get("link", ""),
        }))


 # async def receive(self, text_data=None, bytes_data=None):
    #     """
    #     If you want the client to send messages to the server, you can handle them here.
    #     For notifications, we usually just push from server -> client, so might not be used.
    #     """
    #     # Example: Echo the message or handle commands
    #     if text_data:
    #         data = json.loads(text_data)
    #         action = data.get('action', None)
    #         if action == "ping":
    #             await self.send(text_data=json.dumps({"message": "pong"}))
            
    #         else:
    #             # Handle other client messages if necessary
    #             pass