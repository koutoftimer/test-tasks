from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.db import models

from comments.models import resize_image, attachment_file_path


class FileType(models.TextChoices):
    IMAGE = "image", "Image"
    TEXT = "text", "Text file"


class CommentAttachment(models.Model):
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

    def save(self, *args, **kwargs):
        is_image = self.file and self.file_type == FileType.IMAGE
        fresh_upload = is_image and isinstance(self.file.file, UploadedFile)
        if fresh_upload:
            self.file = resize_image(self.file, *settings.MAX_IMAGE_SIZE)
        super().save(*args, **kwargs)
