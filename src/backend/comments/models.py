import io
import os
import uuid
from datetime import datetime
from typing import cast, Callable

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

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


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    homepage = models.URLField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to=avatar_file_path, blank=True, null=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def save(self, *args, **kwargs):
        if self.avatar:
            self.avatar = resize_image(self.avatar, *settings.MAX_AVATAR_SIZE)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Profile #{self.pk} for {self.user.username}"


def resize_image(file_obj, width, height):
    with Image.open(file_obj) as img:
        if img.format not in ("JPEG", "PNG", "GIF"):
            return file_obj  # TODO: validate image format in serializer
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format=img.format)
        return ContentFile(output.getvalue(), name=file_obj.name)


class FileType(models.TextChoices):
    IMAGE = "image", "Image"
    TEXT = "text", "Text file"


def attachment_file_path(instance, filename):
    _, ext = os.path.splitext(filename)
    name = f"{uuid.uuid4().hex}{ext.lower()}"
    return os.path.join("uploads", datetime.now().strftime("%Y/%m/%d"), name)


class CommentAttachment(models.Model):
    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, related_name="attachments"
    )
    # TODO: add separate field for thumbnails to allow high resolution image attachments
    file = models.FileField(
        upload_to=attachment_file_path, null=True, blank=True, max_length=500
    )
    file_type = models.CharField(
        max_length=10, choices=FileType.choices, null=True, blank=True
    )
    id = models.BigAutoField(primary_key=True)

    class Meta:
        verbose_name = "Comment Attachment"
        verbose_name_plural = "Comment Attachments"
        ordering = ["id"]

    def __str__(self):
        return f"Attachment #{self.pk} for Comment #{self.comment_id}"

    def save(self, *args, **kwargs):
        is_image = self.file and self.file_type == FileType.IMAGE
        fresh_upload = is_image and isinstance(self.file.file, UploadedFile)
        if fresh_upload:
            self.file = resize_image(self.file, *settings.MAX_IMAGE_SIZE)
        super().save(*args, **kwargs)


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
        Profile, on_delete=models.CASCADE, related_name="comments", null=True, blank=True
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


class CommentVote(models.Model):
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_votes"
    )
    vote = models.BooleanField(null=True)

    class Meta:
        unique_together = ("comment", "user")
        verbose_name = "Comment Vote"
        verbose_name_plural = "Comment Votes"
        indexes = [
            models.Index(fields=["comment", "user", "vote"]),
        ]

    def __str__(self):
        status = "like" if self.vote is True else "dislike" if self.vote is False else "removed"
        return f"{status} by {self.user.username} on Comment #{self.comment_id}"


@receiver(post_save, sender=get_user_model())
def create_profile_for_user(sender, instance, created, **kwargs):
    """Create Profile for new users (during registration)."""
    if created:
        Profile.objects.get_or_create(user=instance)
