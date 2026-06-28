import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone

from django_lifecycle import LifecycleModelMixin, hook, BEFORE_CREATE

from comments.models import resize_image, attachment_file_path


class FileType(models.TextChoices):
    IMAGE = "image", "Image"
    TEXT = "text", "Text file"


class CommentAttachment(LifecycleModelMixin, models.Model):
    comment = models.ForeignKey(
        "Comment",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=True,
        blank=True,
    )
    file = models.FileField(
        upload_to=attachment_file_path, null=True, blank=True, max_length=500
    )
    file_type = models.CharField(
        max_length=10, choices=FileType.choices, null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "comments"
        verbose_name = "Comment Attachment"
        verbose_name_plural = "Comment Attachments"
        ordering = ["id"]

    def __str__(self):
        cid = self.comment_id or "?"
        return f"Attachment #{self.pk} for Comment #{cid}"

    @staticmethod
    def delete_orphans():
        cutoff = timezone.now() - datetime.timedelta(hours=3)
        CommentAttachment.objects.filter(
            comment__isnull=True, uploaded_at__lt=cutoff
        ).delete()

    @hook(BEFORE_CREATE)
    def resize_image_attachment(self):
        if self.file_type == FileType.IMAGE:
            self.file = resize_image(self.file, *settings.MAX_IMAGE_SIZE)
