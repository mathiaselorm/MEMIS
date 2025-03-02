# from django.test import TestCase, AsyncTestCase
# from django.contrib.auth import get_user_model
# from .models import MaintenanceSchedule
# from notification.models import Notification
# from django.db.models.signals import post_save
# from channels.testing import WebsocketCommunicator
# from notification.consumers import NotificationConsumer
# import asyncio

# User = get_user_model()

# class MaintenanceScheduleSignalTests(TestCase):
#     def setUp(self):
#         self.user = User.objects.create(username='technician', email='tech@example.com')

#     def test_maintenance_schedule_creation_sends_notification(self):
#         # Connect a mock receiver to the signal to test if it's called
#         def mock_receiver(sender, **kwargs):
#             self.assertIsNotNone(kwargs['instance'])
#             self.assertTrue(kwargs['created'])

#         post_save.connect(mock_receiver, sender=MaintenanceSchedule)

#         # Create a MaintenanceSchedule instance to trigger the signal
#         schedule = MaintenanceSchedule.objects.create(
#             title="Test Maintenance",
#             technician=self.user
#         )

#         # Check that the notification was created
#         notification = Notification.objects.last()
#         self.assertIsNotNone(notification)
#         self.assertEqual(notification.user, self.user)
#         self.assertIn("New maintenance schedule created", notification.message)

#         # Disconnect mock receiver
#         post_save.disconnect(mock_receiver, sender=MaintenanceSchedule)

# class NotificationConsumerTests(AsyncTestCase):
#     async def test_notification_consumer(self):
#         # Create a user for the test
#         user = User.objects.create_user(username='testuser', password='testpass')
#         communicator = WebsocketCommunicator(NotificationConsumer.as_asgi(), f"/ws/notifications/")
#         communicator.scope['user'] = user

#         connected, _ = await communicator.connect()
#         self.assertTrue(connected)

#         # Test sending a message
#         await communicator.send_json_to({
#             "type": "notification.message",
#             "message": "Test Notification",
#             "link": "http://example.com"
#         })

#         # Test receiving the message
#         response = await communicator.receive_json_from()
#         self.assertEqual(response, {
#             "title": "",  # Modify this as needed if your actual implementation includes 'title'
#             "message": "Test Notification",
#             "link": "http://example.com",
#         })

#         # Close the connection
#         await communicator.disconnect()
