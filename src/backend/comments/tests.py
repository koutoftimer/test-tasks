from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from PIL import Image
from captcha.models import CaptchaStore
from rest_framework.test import APIClient

from attachments.models import CommentAttachment


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
