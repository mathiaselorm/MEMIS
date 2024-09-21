from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from assets.models import Asset, Department

User = get_user_model()  # This gets your custom user model

class AuditLogAPITests(APITestCase):

    def setUp(self):
        # Adjust user creation to match your CustomUser model's required fields
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
        # Ensure that the expected key is present in the response data
        self.assertTrue(any('timestamp' in entry for entry in response.data))

    def test_get_actionlogs_accessible_by_authenticated_user(self):
        url = reverse('action-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure that the expected key is present in the response data
        self.assertTrue(any('action' in entry for entry in response.data))

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
