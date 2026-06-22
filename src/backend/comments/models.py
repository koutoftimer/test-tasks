import io
import os
import re
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image


def comment_file_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    name = f"{uuid.uuid4().hex}{'.' + ext if ext else ''}"
    return os.path.join("uploads", datetime.now().strftime("%Y/%m/%d"), name)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    homepage = models.URLField(max_length=200, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return self.user.username


def resize_image(file_obj):
    img = Image.open(file_obj)
    if img.format not in ("JPEG", "PNG", "GIF"):
        return file_obj
    max_w, max_h = settings.MAX_IMAGE_SIZE
    if img.width > max_w or img.height > max_h:
        ratio = min(max_w / img.width, max_h / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format=img.format)
        return ContentFile(output.getvalue(), name=file_obj.name)
    return file_obj


class Comment(models.Model):
    FILE_TYPE_CHOICES = [
        ("image", "Image"),
        ("text", "Text file"),
    ]

    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="comments"
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
    file = models.FileField(
        upload_to=comment_file_path, null=True, blank=True, max_length=500
    )
    file_type = models.CharField(
        max_length=10, choices=FILE_TYPE_CHOICES, null=True, blank=True
    )

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["id"]

    def __str__(self):
        return f"Comment #{self.id} by {self.profile.user.username}"

    def save(self, *args, **kwargs):
        self.strip_unallowed_html()
        if self.file and self.file_type == "image":
            self.file = resize_image(self.file)
        super().save(*args, **kwargs)

    def strip_unallowed_html(self):
        allowed_tags = settings.ALLOWED_HTML_TAGS
        tag_pattern = re.compile(r"<\/?(\w+)([^>]*)>")

        def replace_tag(match):
            tag_name = match.group(1).lower()
            if tag_name not in allowed_tags:
                return ""
            attrs_str = match.group(2).strip()
            if not attrs_str:
                return f"<{tag_name}>"
            allowed_attrs = allowed_tags[tag_name]
            attr_pattern = re.compile(r'(\w+)=(["\'])(.*?)\2')
            clean_attrs = []
            for attr_match in attr_pattern.finditer(attrs_str):
                attr_name = attr_match.group(1).lower()
                if attr_name in allowed_attrs:
                    clean_attrs.append(attr_match.group(0))
            attrs = " " + " ".join(clean_attrs) if clean_attrs else ""
            return f"<{tag_name}{attrs}>"

        self.text = tag_pattern.sub(replace_tag, self.text)

        allowed_tag_names = set(allowed_tags.keys())
        stack = []
        for m in re.finditer(r"<\/?(\w+)", self.text):
            tag = m.group(1).lower()
            if tag not in allowed_tag_names:
                continue
            full = self.text[m.start() : m.end()]
            if m.group(0).startswith("</"):
                if stack and stack[-1] == tag:
                    stack.pop()
                continue
            if not self.text[m.end() : m.end() + 1] == ">":
                continue
            opening_tag = self.text[m.start() : self.text.index(">", m.start()) + 1]
            if opening_tag.endswith("/>"):
                continue
            stack.append(tag)
        for tag in reversed(stack):
            self.text += f"</{tag}>"
