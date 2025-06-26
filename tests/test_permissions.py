# tests/test_permissions.py
from django.test import TestCase
from rest_framework.test import APIClient
from job_app.models import User
from rest_framework import status
from django.urls import reverse

class IsSelfOrAdminPermissionTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='candidate'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123',
            user_type='admin',
            is_staff=True
        )
        self.user_url = reverse('user-detail', kwargs={'pk': self.user.id})

    def test_regular_user_can_delete_self(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_regular_user_cannot_delete_others(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='otherpass123'
        )
        other_url = reverse('user-detail', kwargs={'pk': other_user.id})
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(other_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_any_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_unauthenticated_cannot_delete(self):
        response = self.client.delete(self.user_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)