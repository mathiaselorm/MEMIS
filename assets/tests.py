from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from assets.models import Asset, Department

User = get_user_model()  # This gets your custom user model

class AuditLogAPITests(APITestCase):

    def setUp(self):
        # Assuming 'email' is the username field in your custom user model.
        self.user = User.objects.create_user(email='user@test.com', password='user123')
        self.admin_user = User.objects.create_superuser(email='admin@test.com', password='admin123')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Optionally, create some log entries if needed
        Department.objects.create(name="IT", head=self.admin_user)
        Asset.objects.create(name="Laptop", department=Department.objects.first(), added_by=self.admin_user)

    def test_get_auditlogs_accessible_by_authenticated_user(self):
        url = reverse('audit-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if 'timestamp' or another expected key is in the response
        # Adjust the key according to the actual response format
        self.assertIn('timestamp', response.data[0] if response.data else 'Timestamp key missing')

    def test_get_actionlogs_accessible_by_authenticated_user(self):
        url = reverse('action-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Adjust 'action' to the actual key in your response data
        self.assertIn('action', response.data[0] if response.data else 'Action key missing')

    def test_auditlogs_unauthorized_access(self):
        # Testing unauthorized access by unauthenticated requests
        self.client.logout()  # Logout to simulate an unauthenticated user
        url = reverse('audit-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_actionlogs_unauthorized_access(self):
        # Testing unauthorized access by unauthenticated requests
        self.client.logout()  # Logout to simulate an unauthenticated user
        url = reverse('action-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
