import os

from django.utils import timezone
from rest_framework import serializers

from .models import Comment
from accounts.serializers import ProfileSerializer
from attachments.serializers import CommentAttachmentSerializer


class CommentListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, allow_null=True)
    reply_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    attachments = CommentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "profile",
            "text",
            "parent",
            "created_at",
            "attachments",
            "reply_count",
            "like_count",
            "dislike_count",
            "is_liked",
            "is_disliked",
        ]

    def get_reply_count(self, obj):
        return obj.replies.count()

    def get_like_count(self, obj):
        if hasattr(obj, "like_count"):
            return obj.like_count
        return obj.votes.filter(vote=True).count()

    def get_dislike_count(self, obj):
        if hasattr(obj, "dislike_count"):
            return obj.dislike_count
        return obj.votes.filter(vote=False).count()

    def get_is_liked(self, obj):
        return getattr(obj, "is_liked", False)

    def get_is_disliked(self, obj):
        return getattr(obj, "is_disliked", False)


class CommentDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, allow_null=True)
    replies = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    attachments = CommentAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "profile",
            "text",
            "parent",
            "created_at",
            "attachments",
            "replies",
            "like_count",
            "dislike_count",
            "is_liked",
            "is_disliked",
        ]

    def get_replies(self, obj):
        replies = obj.replies.all().order_by("id")
        if replies:
            return CommentDetailSerializer(
                replies, many=True, context=self.context
            ).data
        return []

    def get_like_count(self, obj):
        if hasattr(obj, "like_count"):
            return obj.like_count
        return obj.votes.filter(vote=True).count()

    def get_dislike_count(self, obj):
        if hasattr(obj, "dislike_count"):
            return obj.dislike_count
        return obj.votes.filter(vote=False).count()

    def get_is_liked(self, obj):
        return getattr(obj, "is_liked", False)

    def get_is_disliked(self, obj):
        return getattr(obj, "is_disliked", False)


def _validate_single_file(file):
    _, ext = os.path.splitext(file.name.lower())
    ext = ext.lstrip(".") if ext else ""
    if ext not in ("jpg", "jpeg", "png", "gif", "txt"):
        raise serializers.ValidationError(
            "Only JPG, GIF, PNG, and TXT files are allowed."
        )
    if ext == "txt" and file.size > 100 * 1024:
        raise serializers.ValidationError("Text file exceeds maximum size of 100KB.")
    return file


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    files = serializers.ListField(
        child=serializers.FileField(), required=False, allow_empty=True
    )
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Text is required.")
        return value

    def validate_files(self, value):
        if value:
            for f in value:
                _validate_single_file(f)
        return value

    def validate_parent_id(self, value):
        if value is not None and not Comment.objects.filter(id=value).exists():
            raise serializers.ValidationError("Parent comment does not exist.")
        return value

    def validate(self, attrs):
        from captcha.models import CaptchaStore

        try:
            store = CaptchaStore.objects.get(
                hashkey=attrs["captcha_key"],
                response__iexact=attrs["captcha_value"],
                expiration__gt=timezone.now(),
            )
            store.delete()
        except CaptchaStore.DoesNotExist:
            raise serializers.ValidationError(
                {"captcha_value": "Invalid or expired CAPTCHA."}
            )
        return attrs

    def _get_file_type(self, file):
        _, ext = os.path.splitext(file.name.lower())
        ext = ext.lstrip(".") if ext else ""
        if ext in ("jpg", "jpeg", "png", "gif"):
            return "image"
        if ext == "txt":
            return "text"
        return None

    def create(self, validated_data):
        from accounts.models import Profile
        from attachments.models import CommentAttachment

        text = validated_data["text"]
        parent_id = validated_data.get("parent_id")
        files = validated_data.get("files", [])

        request = self.context.get("request")
        profile = None
        if request and request.user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=request.user)

        parent = None
        if parent_id:
            parent = Comment.objects.get(id=parent_id)

        comment = Comment.objects.create(
            profile=profile,
            text=text,
            parent=parent,
        )

        for f in files:
            CommentAttachment.objects.create(
                comment=comment,
                file=f,
                file_type=self._get_file_type(f),
            )

        return comment

    def to_representation(self, instance):
        return CommentDetailSerializer(instance, context=self.context).data
