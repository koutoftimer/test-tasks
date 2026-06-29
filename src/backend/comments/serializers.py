from django.utils import timezone
from rest_framework import serializers

from .models import Comment
from accounts.serializers import ProfileSerializer
from attachments.models import CommentAttachment


class CommentListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, allow_null=True)
    reply_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    dislike_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "profile",
            "text",
            "parent",
            "created_at",
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

    class Meta:
        model = Comment
        fields = [
            "id",
            "profile",
            "text",
            "parent",
            "created_at",
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


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)
    attachment_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CommentAttachment.objects.filter(comment__isnull=True),
        required=False,
        write_only=True,
    )

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Text is required.")
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

    def create(self, validated_data):
        from accounts.models import Profile

        text = validated_data["text"]
        parent_id = validated_data.get("parent_id")
        attachment_ids = validated_data.get("attachment_ids")

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

        if attachment_ids:
            CommentAttachment.objects.filter(
                id__in=[att.id for att in attachment_ids],
            ).update(comment=comment)

        return comment

    def to_representation(self, instance):
        return CommentDetailSerializer(instance, context=self.context).data
