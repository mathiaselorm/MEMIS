# tests/test_consumers.py
import pytest
from channels.testing import WebsocketCommunicator
from notification.consumers import NotificationConsumer
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

@pytest.mark.django_db
@pytest.mark.asyncio
async def test_notification_consumer():
    user = await sync_to_async(get_user_model().objects.create_user)(
        username='testuser', password='testpass'
    )
    communicator = WebsocketCommunicator(
        NotificationConsumer.as_asgi(),
        "/ws/notifications/"
    )
    communicator.scope['user'] = user

    connected, subprotocol = await communicator.connect()
    assert connected

    await communicator.send_json_to({
        "type": "notification.message",
        "message": "Test Notification",
        "link": "http://example.com"
    })

    response = await communicator.receive_json_from()
    assert response == {
        "title": "",
        "message": "Test Notification",
        "link": "http://example.com",
    }

    await communicator.disconnect()
