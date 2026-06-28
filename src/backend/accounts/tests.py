from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework.test import APIClient


class TestUser(TestCase):
    def setUp(self):
        self.test_user1 = User.objects.create_user(
            username="test1", email="test1@example.com", password="pass"
        )

    def test_authentication(self):
        """POST /api/auth/jwt/create/ returns access and refresh tokens."""
        response = self.client.post(
            reverse("jwt-create"), data={"username": "test1", "password": "pass"}
        )
        self.assertEqual(response.status_code, 200)
        tokens = response.json()
        self.assertTrue("access" in tokens)
        self.assertTrue("refresh" in tokens)


class TestProfile(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.test_user1 = User.objects.create_user(
            username="test1", email="test1@example.com", password="pass"
        )
        self.test_user2 = User.objects.create_user(
            username="test2", email="test2@example.com", password="pass"
        )

    def _authentication_header(self, tokens: dict[str, str]) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens['access']}"}

    def _authorize(self) -> dict[str, str]:
        response = self.client.post(
            reverse("jwt-create"), data={"username": "test1", "password": "pass"}
        )
        return response.json()

    def test_user_created_with_profile(self):
        """post_save signal creates a Profile for every new User."""
        self.assertTrue(self.test_user1.profile)
        self.assertTrue(self.test_user2.profile)

    def test_edit_only_personal_profile(self):
        """PATCH own profile returns 200; PATCH another user's profile returns 403."""
        tokens = self._authorize()
        headers = self._authentication_header(tokens)

        path = reverse("profile-detail", args=[self.test_user1.profile.id])
        data = {"email": "new-mail@example.com"}

        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], data["email"])
        self.assertEqual(User.objects.get(pk=self.test_user1.pk).email, data["email"])

        path = reverse("profile-detail", args=[self.test_user2.profile.id])
        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_retrieve_own_profile(self):
        """GET own profile returns 200 with email, homepage, and avatar fields."""
        tokens = self._authorize()
        response = self.client.get(
            reverse("profile-detail", args=[self.test_user1.profile.id]),
            headers=self._authentication_header(tokens),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("email", data)
        self.assertIn("homepage", data)
        self.assertIn("avatar", data)

    def test_retrieve_other_profile(self):
        """GET another user's profile returns 403."""
        tokens = self._authorize()
        response = self.client.get(
            reverse("profile-detail", args=[self.test_user2.profile.id]),
            headers=self._authentication_header(tokens),
        )
        self.assertEqual(response.status_code, 403)

    def test_retrieve_profile_unauthenticated(self):
        """GET profile without JWT returns 401."""
        response = self.client.get(
            reverse("profile-detail", args=[self.test_user1.profile.id]),
        )
        self.assertEqual(response.status_code, 401)

    def test_update_homepage(self):
        """PATCH homepage returns 200 and persists the new value in DB."""
        tokens = self._authorize()
        headers = self._authentication_header(tokens)
        path = reverse("profile-detail", args=[self.test_user1.profile.id])
        data = {"homepage": "https://example.com"}

        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.test_user1.profile.refresh_from_db()
        self.assertEqual(self.test_user1.profile.homepage, "https://example.com")

    def test_update_email_persists(self):
        """PATCH email returns 200 and persists on the User model in DB."""
        tokens = self._authorize()
        headers = self._authentication_header(tokens)
        path = reverse("profile-detail", args=[self.test_user1.profile.id])
        data = {"email": "updated@example.com"}

        response = self.client.patch(path=path, data=data, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            User.objects.get(pk=self.test_user1.pk).email, "updated@example.com"
        )

    def test_update_homepage_empty_string(self):
        """PATCH homepage="" stores None in DB (via the or None logic)."""
        tokens = self._authorize()
        headers = self._authentication_header(tokens)
        path = reverse("profile-detail", args=[self.test_user1.profile.id])

        self.client.patch(
            path=path, data={"homepage": "https://example.com"}, headers=headers
        )
        response = self.client.patch(path=path, data={"homepage": ""}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.test_user1.profile.refresh_from_db()
        self.assertIsNone(self.test_user1.profile.homepage)

    def test_update_nonexistent_profile(self):
        """PATCH on a non-existent profile ID returns 404."""
        tokens = self._authorize()
        response = self.client.patch(
            reverse("profile-detail", args=[99999]),
            data={"email": "x@x.com"},
            headers=self._authentication_header(tokens),
        )
        self.assertEqual(response.status_code, 404)

    def test_update_without_auth(self):
        """PATCH profile without JWT returns 401."""
        response = self.client.patch(
            reverse("profile-detail", args=[self.test_user1.profile.id]),
            data={"email": "x@x.com"},
        )
        self.assertEqual(response.status_code, 401)

    def test_method_not_allowed(self):
        """POST and DELETE on profile return 405."""
        tokens = self._authorize()
        headers = self._authentication_header(tokens)
        path = reverse("profile-detail", args=[self.test_user1.profile.id])

        response = self.client.post(path=path, data={}, headers=headers)
        self.assertEqual(response.status_code, 405)

        response = self.client.delete(path=path, headers=headers)
        self.assertEqual(response.status_code, 405)

    def test_profile_created_on_user_registration(self):
        """POST /api/auth/users/ (register) triggers signal and creates Profile."""
        response = self.client.post(
            reverse("user-list"),
            data={
                "username": "newuser",
                "password": "secret123",
                "email": "new@example.com",
            },
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "profile"))

    def test_user_serializer_has_profile_id(self):
        """GET /api/auth/users/me/ includes profile_id in the response."""
        tokens = self._authorize()
        response = self.client.get(
            reverse("user-me"),
            headers=self._authentication_header(tokens),
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("profile_id", data)
        self.assertEqual(data["profile_id"], self.test_user1.profile.id)
