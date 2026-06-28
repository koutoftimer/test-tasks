from rest_framework import serializers

from .models import CommentAttachment


class CommentAttachmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommentAttachment
        fields = ["id", "file", "file_type"]
