# notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser



class NotificationConsumer(AsyncWebsocketConsumer):
    """
    A consumer that handles real-time notifications for an authenticated user
    using a custom JWTAuthMiddlewareStack.
    """

    async def connect(self):
        self.user = self.scope.get("user", None)

        # If the user is not authenticated, close the socket
        if not self.user or isinstance(self.user, AnonymousUser):
            await self.close()
            return

        # Create a unique group name based on user.id
        self.group_name = f"notification_user_{self.user.id}"

        # Add this channel to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

    async def disconnect(self, close_code):
        # Remove channel from group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

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

    async def notification_message(self, event):
        """
        This method is called whenever a message is sent to this user's group.
        event structure might be:
        {
            "type": "notification_message",
            "title": "some title",
            "message": "some message",
            "link": "...",
        }
        """
        await self.send(text_data=json.dumps({
            "title": event.get("title", ""),
            "message": event.get("message", ""), 
            "link": event.get("link", ""),
        }))
