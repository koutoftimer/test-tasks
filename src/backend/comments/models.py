import io
import os
import uuid
from datetime import datetime
from typing import cast, Callable

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

from html_sanitizer import Sanitizer
from PIL import Image


# TODO: Maybe functools.partial will be handier
def upload_file_path(prefix: str) -> Callable[[models.Model, str], str]:
    """Return Callable that returns <prefix>/%Y/%d/%m/<uuid4>.<filename extension>"""
    def file_path(instance: models.Model, filename: str) -> str:
        _, ext = os.path.splitext(filename)
        name = f"{uuid.uuid4().hex}{ext.lower()}"
        return os.path.join(prefix, datetime.now().strftime("%Y/%m/%d"), name)
    return file_path


# Required for migrations: ./migrations/0002_add_comment_vote.py
comment_file_path = cast(str, upload_file_path('uploads'))
# Required for migrations: ./migrations/0004_alter_profile_avatar_and_more.py
avatar_file_path = cast(str, upload_file_path('avatars'))
# Required for migrations: ./migrations/0005_add_comment_attachment.py
attachment_file_path = cast(str, upload_file_path('uploads'))


def resize_image(file_obj, width, height):
    with Image.open(file_obj) as img:
        if img.format not in ("JPEG", "PNG", "GIF"):
            return file_obj  # TODO: validate image format in serializer
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format=img.format)
        return ContentFile(output.getvalue(), name=file_obj.name)


def sanitize_text(text):
    allowed_tags = settings.ALLOWED_HTML_TAGS
    sanitizer = Sanitizer({
        "tags": set(allowed_tags.keys()),
        "attributes": {tag: set(attrs) for tag, attrs in allowed_tags.items()},
        "empty": {"br"},
        "separate": set(allowed_tags.keys()) - {"br"},
        "sanitize_href": lambda href: href,
    })
    return sanitizer.sanitize(text)


class Comment(models.Model):
    profile = models.ForeignKey(
        "comments.Profile", on_delete=models.CASCADE, related_name="comments", null=True, blank=True
    )
    text = models.TextField()
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["id"]

    def __str__(self):
        if not self.profile_id:
            return f"Comment #{self.id} by Anonymous"
        return f"Comment #{self.id} by {self.profile.user.username}"

    def save(self, *args, **kwargs):
        self.strip_unallowed_html()
        super().save(*args, **kwargs)

    def strip_unallowed_html(self):
        self.text = sanitize_text(self.text)



