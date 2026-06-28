from django.conf import settings
from django.db import models

from django_lifecycle import LifecycleModelMixin, hook, BEFORE_CREATE

from comments.models import resize_image, attachment_file_path


class FileType(models.TextChoices):
    IMAGE = "image", "Image"
    TEXT = "text", "Text file"


class CommentAttachment(LifecycleModelMixin, models.Model):
    comment = models.ForeignKey(
        "Comment", on_delete=models.CASCADE, related_name="attachments"
    )
    file = models.FileField(
        upload_to=attachment_file_path, null=True, blank=True, max_length=500
    )
    file_type = models.CharField(
        max_length=10, choices=FileType.choices, null=True, blank=True
    )

    class Meta:
        app_label = "comments"
        verbose_name = "Comment Attachment"
        verbose_name_plural = "Comment Attachments"
        ordering = ["id"]

    def __str__(self):
        return f"Attachment #{self.pk} for Comment #{self.comment_id}"

    @hook(BEFORE_CREATE)
    def resize_image_if_needed(self):
        if self.file and self.file_type == FileType.IMAGE:
            self.file = resize_image(self.file, *settings.MAX_IMAGE_SIZE)
