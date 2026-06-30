import io
import struct
import zlib
from datetime import timedelta

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from PIL import Image
from rest_framework.test import APIClient

from comments.models import Comment


def _make_image(name="test.png", width=640, height=480):
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color="red").save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


def _make_text(name="test.txt", content="Hello, world!"):
    return SimpleUploadedFile(name, content.encode(), content_type="text/plain")


class TestUpload(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("upload-list")

    def test_upload_image(self):
        """POST /api/upload/ with a PNG returns 201, file_type="image"."""
        response = self.client.post(
            self.url, {"file": _make_image()}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("file", data)
        self.assertEqual(data["file_type"], "image")

    def test_upload_text_file(self):
        """POST /api/upload/ with a .txt returns 201, file_type="text"."""
        response = self.client.post(
            self.url, {"file": _make_text()}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("file", data)
        self.assertEqual(data["file_type"], "text")

    def test_upload_unsupported_extension(self):
        """POST /api/upload/ with a .pdf returns 400."""
        f = SimpleUploadedFile("test.pdf", b"fake pdf", content_type="application/pdf")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_text_file_too_large(self):
        """POST /api/upload/ with a .txt >100KB returns 400."""
        content = b"x" * (settings.MAX_TEXT_FILE_SIZE + 1)
        f = _make_text(name="large.txt", content=content.decode())
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_without_auth(self):
        """POST /api/upload/ without JWT returns 201 (open endpoint)."""
        response = self.client.post(
            self.url, {"file": _make_image()}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)

    def test_response_format(self):
        """Response contains id (int), file (str), file_type (str)."""
        response = self.client.post(
            self.url, {"file": _make_image()}, format="multipart"
        )
        data = response.json()
        self.assertCountEqual(data.keys(), {"id", "file", "file_type"})
        self.assertIsInstance(data["id"], int)
        self.assertIsInstance(data["file"], str)
        self.assertIsInstance(data["file_type"], str)

    def test_image_resized(self):
        """Uploaded 640x480 image is resized to ≤320x240 via @hook(BEFORE_CREATE)."""
        from .models import CommentAttachment

        response = self.client.post(
            self.url, {"file": _make_image(width=640, height=480)}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)

        att = CommentAttachment.objects.get(pk=response.json()["id"])
        img = Image.open(att.file)
        max_w, max_h = settings.MAX_IMAGE_SIZE
        self.assertLessEqual(img.width, max_w)
        self.assertLessEqual(img.height, max_h)

    def test_text_file_not_resized(self):
        """Uploaded .txt content is unchanged (resize hook skips non-images)."""
        from .models import CommentAttachment

        response = self.client.post(
            self.url, {"file": _make_text(content="A" * 5000)}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)

        att = CommentAttachment.objects.get(pk=response.json()["id"])
        content = att.file.read()
        self.assertEqual(len(content), 5000)

    def test_upload_zero_byte_image(self):
        """Empty .png file returns 400."""
        f = SimpleUploadedFile("empty.png", b"", content_type="image/png")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_no_extension(self):
        """File without extension returns 400."""
        f = SimpleUploadedFile("test", b"x", content_type="text/plain")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_trailing_dot(self):
        """File named 'test.' (trailing dot, no extension) returns 400."""
        f = SimpleUploadedFile("test.", b"x", content_type="text/plain")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_corrupt_image(self):
        """Random bytes with .png extension returns 400."""
        f = SimpleUploadedFile("corrupt.png", b"\x00\x01\x02" * 21, content_type="image/png")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_truncated_image(self):
        """Valid PNG header with truncated body returns 400."""
        buf = io.BytesIO()
        Image.new("RGB", (1, 1), color="red").save(buf, format="PNG")
        full = buf.getvalue()
        f = SimpleUploadedFile("truncated.png", full[:30], content_type="image/png")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_upload_image_too_large(self):
        """Image >5MB returns 400."""
        size = 5 * 1024 * 1024 + 1
        f = SimpleUploadedFile("large.png", b"x" * size, content_type="image/png")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def _make_png_bomb(self, width=65535, height=65535):
        """Craft a minimal PNG declaring extreme dimensions."""
        def chunk(chunk_type, data):
            c = chunk_type + data
            return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

        sig = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        raw = zlib.compress(b"\x00\x00\x00\x00")
        idat = chunk(b"IDAT", raw)
        iend = chunk(b"IEND", b"")
        return sig + ihdr + idat + iend

    def test_upload_decompression_bomb(self):
        """A PNG with extreme dimensions is rejected as invalid image (400)."""
        data = self._make_png_bomb(65535, 65535)
        f = SimpleUploadedFile("bomb.png", data, content_type="image/png")
        response = self.client.post(self.url, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 400)

    def test_orphan_cleanup_old(self):
        """Orphan attachment (>3h old, no comment) deleted on next upload."""
        from .models import CommentAttachment

        old = CommentAttachment.objects.create(file=_make_image())
        CommentAttachment.objects.filter(pk=old.pk).update(
            uploaded_at=timezone.now() - timedelta(hours=4)
        )
        self.client.post(self.url, {"file": _make_image()}, format="multipart")
        self.assertFalse(CommentAttachment.objects.filter(pk=old.pk).exists())

    def test_orphan_cleanup_recent(self):
        """Recent orphan (<3h old, no comment) preserved on next upload."""
        from .models import CommentAttachment

        recent = CommentAttachment.objects.create(file=_make_image())
        self.client.post(self.url, {"file": _make_image()}, format="multipart")
        self.assertTrue(CommentAttachment.objects.filter(pk=recent.pk).exists())

    def test_orphan_cleanup_with_comment(self):
        """Attached attachment (has comment, >3h old) preserved on next upload."""
        from .models import CommentAttachment

        comment = Comment.objects.create(text="Parent")
        attached = CommentAttachment.objects.create(file=_make_image(), comment=comment)
        CommentAttachment.objects.filter(pk=attached.pk).update(
            uploaded_at=timezone.now() - timedelta(hours=4)
        )
        self.client.post(self.url, {"file": _make_image()}, format="multipart")
        self.assertTrue(CommentAttachment.objects.filter(pk=attached.pk).exists())
