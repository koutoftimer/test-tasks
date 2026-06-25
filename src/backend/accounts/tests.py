from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APIClient


class TestUser(TestCase):
    def setUp(self):
        self.test_user1 = User.objects.create_user(username="test1", email="test1@example.com", password="pass")

    def test_authentication(self):
        response = self.client.post(reverse('jwt-create'), data={"username": "test1", "password": "pass"})
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertTrue('access' in tokens)
        self.assertTrue('refresh' in tokens)


class TestProfile(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user1 = User.objects.create_user(username="test1", email="test1@example.com", password="pass")
        self.test_user2 = User.objects.create_user(username="test2", email="test2@example.com", password="pass")

    def _authentication_header(self, tokens: dict[str, str]) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens['access']}"}

    def _authorize(self) -> dict[str, str]:
        response = self.client.post(reverse('jwt-create'), data={"username": "test1", "password": "pass"})
        return response.json()

    def test_user_created_with_profile(self):
        self.assertTrue(self.test_user1.profile)
        self.assertTrue(self.test_user2.profile)

    def test_edit_only_personal_profile(self):
        tokens = self._authorize()

        path = reverse('profile-detail', args=[self.test_user1.profile.id])
        headers = headers=self._authentication_header(tokens)
        data = {"email": "new-mail@example.com"}

        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['email'], data['email'])

        path = reverse('profile-detail', args=[self.test_user2.profile.id])
        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 403)
