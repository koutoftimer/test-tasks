import os

from django.conf import settings
from rest_framework import serializers

from comments.models import IMAGE_EXTENSIONS, SUPPORTED_EXTENSIONS
from .models import CommentAttachment, FileType


class CommentAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentAttachment
        fields = ["id", "file", "file_type"]


class UploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentAttachment
        fields = ["id", "file", "file_type"]
        read_only_fields = ["file_type"]

    def validate_file(self, value):
        _, ext = os.path.splitext(value.name.lower())
        if ext not in SUPPORTED_EXTENSIONS:
            raise serializers.ValidationError(
                "Only JPG, GIF, PNG, and TXT files are allowed."
            )
        is_text_file = ext not in IMAGE_EXTENSIONS
        if is_text_file and value.size > settings.MAX_TEXT_FILE_SIZE:
            raise serializers.ValidationError(
                "Text file exceeds maximum size of 100KB."
            )
        return value

    def create(self, validated_data):
        file = validated_data["file"]
        _, ext = os.path.splitext(file.name.lower())
        validated_data["file_type"] = (
            FileType.IMAGE if ext in IMAGE_EXTENSIONS else FileType.TEXT
        )
        return super().create(validated_data)
