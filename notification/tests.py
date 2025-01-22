# from django.urls import reverse
# from rest_framework.test import APITestCase
# from rest_framework import status
# from accounts.models import CustomUser, AuditLog
# from notification.models import Notification


# class NotificationSystemTests(APITestCase):
#     def setUp(self):
#         # Create users for testing
#         self.user1 = CustomUser.objects.create_user(
#             email="user1@example.com", password="password123", first_name="User1"
#         )
#         self.user2 = CustomUser.objects.create_user(
#             email="user2@example.com", password="password123", first_name="User2"
#         )
#         self.superuser = CustomUser.objects.create_superuser(
#             email="admin@example.com", password="adminpassword", first_name="Admin"
#         )

#         # Authenticate as user1
#         self.client.force_authenticate(user=self.user1)

#         # Create test notifications
#         self.notification1 = Notification.objects.create(
#             user=self.user1, message="Test Notification 1", link="http://example.com"
#         )
#         self.notification2 = Notification.objects.create(
#             user=self.user1, message="Test Notification 2", link="http://example.com"
#         )

#     def test_user_creation(self):
#         """Test user creation with CustomUser model"""
#         self.assertEqual(CustomUser.objects.count(), 3)
#         self.assertEqual(self.user1.email, "user1@example.com")

#     def test_audit_log_creation(self):
#         """Test that an audit log is created when a user is created"""
#         AuditLog.objects.create(
#             user=self.superuser,
#             action=AuditLog.ActionChoices.CREATE,
#             target_user=self.user1,
#             details="Created user1@example.com",
#         )
#         self.assertEqual(AuditLog.objects.count(), 1)
#         log = AuditLog.objects.first()
#         self.assertEqual(log.action, AuditLog.ActionChoices.CREATE)
#         self.assertEqual(log.target_user, self.user1)

#     def test_notification_list_view(self):
#         """Test listing notifications for an authenticated user"""
#         url = reverse("notification-list")
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 2)

#     def test_notification_detail_view(self):
#         """Test retrieving a single notification"""
#         url = reverse("notification-detail", kwargs={"pk": self.notification1.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["message"], self.notification1.message)

#     def test_mark_notification_as_read(self):
#         """Test marking a notification as read"""
#         url = reverse("notification-detail", kwargs={"pk": self.notification1.pk})
#         response = self.client.patch(url, {"is_read": True})
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.notification1.refresh_from_db()
#         self.assertTrue(self.notification1.is_read)

#     def test_mark_all_notifications_as_read(self):
#         """Test marking all notifications as read"""
#         url = reverse("mark-all-notifications-read")
#         response = self.client.post(url)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         unread_notifications = Notification.objects.filter(user=self.user1, is_read=False)
#         self.assertEqual(unread_notifications.count(), 0)

#     def test_notification_permission(self):
#         """Ensure users cannot access other users' notifications"""
#         self.client.force_authenticate(user=self.user2)
#         url = reverse("notification-detail", kwargs={"pk": self.notification1.pk})
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     def test_audit_log_str(self):
#         """Test the string representation of an audit log"""
#         log = AuditLog.objects.create(
#             user=self.superuser,
#             action=AuditLog.ActionChoices.CREATE,
#             target_user=self.user1,
#             details="Created user1@example.com",
#         )
#         self.assertIn("Admin performed Create User on User1", str(log))
