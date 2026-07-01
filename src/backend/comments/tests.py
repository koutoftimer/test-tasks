from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from PIL import Image
from captcha.models import CaptchaStore
from rest_framework.test import APIClient

from django.contrib.auth.models import User

from attachments.models import CommentAttachment
from comments.models import Comment


def _make_image():
    buf = BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile("test.png", buf.read(), content_type="image/png")


def _make_captcha():
    from captcha.models import CaptchaStore

    return CaptchaStore.objects.create(
        hashkey="captcha-key",
        response="answer",
        expiration=timezone.now() + timedelta(minutes=5),
    )


def _upload_attachment(client):
    response = client.post(
        reverse("upload-list"), {"file": _make_image()}, format="multipart"
    )
    return response.json()


class TestCommentCreate(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("comment-list")
        _make_captcha()

    def _valid_payload(self, overrides=None):
        payload = {
            "text": "Test comment",
            "captcha_key": "captcha-key",
            "captcha_value": "answer",
            "parent_id": None,
        }
        if overrides:
            payload.update(overrides)
        return payload

    def test_create_with_attachments(self):
        """Attachments are assigned to the comment after creation."""
        att1 = _upload_attachment(self.client)
        att2 = _upload_attachment(self.client)

        response = self.client.post(
            self.url,
            self._valid_payload({"attachment_ids": [att1["id"], att2["id"]]}),
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        comment_id = response.json()["id"]
        self.assertTrue(
            CommentAttachment.objects.filter(
                id=att1["id"], comment_id=comment_id
            ).exists()
        )
        self.assertTrue(
            CommentAttachment.objects.filter(
                id=att2["id"], comment_id=comment_id
            ).exists()
        )

    def test_create_without_attachments(self):
        """Comment creation without attachment_ids works."""
        response = self.client.post(self.url, self._valid_payload(), format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_with_empty_attachments(self):
        """Comment creation with attachment_ids=[] works."""
        response = self.client.post(
            self.url,
            self._valid_payload({"attachment_ids": []}),
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_with_nonexistent_attachment(self):
        """Non-existent attachment ID returns 400."""
        response = self.client.post(
            self.url,
            self._valid_payload({"attachment_ids": [99999]}),
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_with_already_assigned_attachment(self):
        """Attachment already linked to another comment returns 400."""
        att = _upload_attachment(self.client)

        first = self.client.post(
            self.url,
            self._valid_payload({"attachment_ids": [att["id"]]}),
            format="json",
        )
        self.assertEqual(first.status_code, 201)

        second = self.client.post(
            self.url,
            self._valid_payload({"attachment_ids": [att["id"]]}),
            format="json",
        )
        self.assertEqual(second.status_code, 400)

    def test_master_captcha_bypasses_validation(self):
        """MASTER_CAPTCHA_VALUE skips CaptchaStore lookup."""
        with self.settings(MASTER_CAPTCHA_VALUE="master-value"):
            resp = self.client.post(
                self.url,
                self._valid_payload({"captcha_value": "master-value"}),
                format="json",
            )
        self.assertEqual(resp.status_code, 201)

    def test_master_captcha_deletes_store_entry(self):
        """Master bypass still removes the CaptchaStore row."""
        with self.settings(MASTER_CAPTCHA_VALUE="master-value"):
            self.client.post(
                self.url,
                self._valid_payload({"captcha_value": "master-value"}),
                format="json",
            )
        self.assertFalse(CaptchaStore.objects.filter(hashkey="captcha-key").exists())

    def test_master_captcha_wrong_value_still_validated(self):
        """Wrong captcha_value goes through normal validation and fails."""
        with self.settings(MASTER_CAPTCHA_VALUE="master-value"):
            resp = self.client.post(
                self.url,
                self._valid_payload({"captcha_value": "wrong"}),
                format="json",
            )
        self.assertEqual(resp.status_code, 400)

    def test_master_captcha_not_set_does_not_bypass(self):
        """Default empty MASTER_CAPTCHA_VALUE doesn't bypass anything."""
        with self.settings(MASTER_CAPTCHA_VALUE=""):
            resp = self.client.post(
                self.url,
                self._valid_payload({"captcha_value": ""}),
                format="json",
            )
        self.assertEqual(resp.status_code, 400)


class TestCommentAuthorDenorm(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("comment-list")
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="pass"
        )
        _make_captcha()

    def _auth_header(self):
        response = self.client.post(
            reverse("jwt-create"),
            data={"username": "testuser", "password": "pass"},
        )
        return {"Authorization": f"Bearer {response.json()['access']}"}

    def _create_comment(self, headers=None):
        payload = {
            "text": "Test comment",
            "captcha_key": "captcha-key",
            "captcha_value": "answer",
        }
        kwargs = {"data": payload, "format": "json"}
        if headers:
            kwargs["headers"] = headers
        return self.client.post(self.url, **kwargs)

    def test_author_fields_set_on_creation(self):
        """Authenticated user's username and email are stored on the comment."""
        response = self._create_comment(headers=self._auth_header())
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get(id=response.json()["id"])
        self.assertEqual(comment.author_username, "testuser")
        self.assertEqual(comment.author_email, "test@example.com")

    def test_anonymous_comment_empty_author_fields(self):
        """Unauthenticated comment gets empty author fields."""
        response = self._create_comment()
        self.assertEqual(response.status_code, 201)
        comment = Comment.objects.get(id=response.json()["id"])
        self.assertEqual(comment.author_username, "")
        self.assertEqual(comment.author_email, "")

    def test_update_username_propagates_to_comments(self):
        """Changing username updates denormalized field on existing comments."""
        response = self._create_comment(headers=self._auth_header())
        comment = Comment.objects.get(id=response.json()["id"])

        self.user.username = "updated_user"
        self.user.save()

        comment.refresh_from_db()
        self.assertEqual(comment.author_username, "updated_user")
        self.assertEqual(comment.author_email, "test@example.com")

    def test_update_email_propagates_to_comments(self):
        """Changing email updates denormalized field on existing comments."""
        response = self._create_comment(headers=self._auth_header())
        comment = Comment.objects.get(id=response.json()["id"])

        self.user.email = "updated@example.com"
        self.user.save()

        comment.refresh_from_db()
        self.assertEqual(comment.author_username, "testuser")
        self.assertEqual(comment.author_email, "updated@example.com")


class TestCommentOrdering(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("comment-list")
        self.c1 = Comment.objects.create(
            text="First", author_username="alpha", author_email="a@test.com"
        )
        self.c2 = Comment.objects.create(
            text="Second", author_username="beta", author_email="b@test.com"
        )
        self.c3 = Comment.objects.create(
            text="Third", author_username="gamma", author_email="c@test.com"
        )

    def _get_ids(self, ordering=None):
        params = {}
        if ordering:
            params["ordering"] = ordering
        response = self.client.get(self.url, params)
        return [c["id"] for c in response.json()["results"]]

    def test_default_ordering(self):
        """Default ordering is -id (newest first)."""
        ids = self._get_ids()
        self.assertEqual(ids, [self.c3.id, self.c2.id, self.c1.id])

    def test_ordering_by_id_asc(self):
        """?ordering=id returns oldest first."""
        ids = self._get_ids("id")
        self.assertEqual(ids, [self.c1.id, self.c2.id, self.c3.id])

    def test_ordering_by_id_desc(self):
        """?ordering=-id returns newest first."""
        ids = self._get_ids("-id")
        self.assertEqual(ids, [self.c3.id, self.c2.id, self.c1.id])

    def test_ordering_by_author_username(self):
        """?ordering=author_username sorts alphabetically by username."""
        ids = self._get_ids("author_username")
        self.assertEqual(ids, [self.c1.id, self.c2.id, self.c3.id])

    def test_ordering_by_author_username_desc(self):
        """?ordering=-author_username sorts reverse alphabetically."""
        ids = self._get_ids("-author_username")
        self.assertEqual(ids, [self.c3.id, self.c2.id, self.c1.id])

    def test_ordering_by_author_email(self):
        """?ordering=author_email sorts alphabetically by email."""
        ids = self._get_ids("author_email")
        self.assertEqual(ids, [self.c1.id, self.c2.id, self.c3.id])

    def test_ordering_invalid_field(self):
        """Invalid ordering field falls back to default ordering (-id)."""
        ids = self._get_ids("nonexistent")
        self.assertEqual(ids, [self.c3.id, self.c2.id, self.c1.id])

    def test_ordering_preserves_pagination(self):
        """Response with ordering param still includes pagination fields."""
        response = self.client.get(self.url, {"ordering": "author_username"})
        data = response.json()
        self.assertIn("count", data)
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)
