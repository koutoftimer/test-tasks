from django.conf import settings
from django.utils import timezone

from rest_framework import serializers

from .models import Comment
from accounts.serializers import ProfileSerializer
from attachments.models import CommentAttachment
from likes.redis_service import get_vote_counts


class CommentListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, allow_null=True)
    reply_count = serializers.SerializerMethodField()
    # this fields should be populated with annotation
    like_count = serializers.IntegerField(read_only=True)
    dislike_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_disliked = serializers.BooleanField(read_only=True)

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


class CommentDetailSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True, allow_null=True)
    replies = serializers.SerializerMethodField()
    # this fields shouls be populated with annotation from Redis
    like_count = serializers.IntegerField(read_only=True)
    dislike_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.BooleanField(read_only=True)
    is_disliked = serializers.BooleanField(read_only=True)

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
        # We need a method here because we need to attach redis data
        # to the nested replies before they are serialized
        replies = obj.replies.all().select_related("profile__user").order_by("id")

        # Access the viewset method to attach redis data to this sub-list
        view = self.context.get("view")
        if view and hasattr(view, "_attach_votes_from_redis"):
            view._attach_votes_from_redis(replies)

        return CommentDetailSerializer(replies, many=True, context=self.context).data


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

        captcha_value = attrs["captcha_value"]
        captcha_key = attrs["captcha_key"]

        if (
            settings.MASTER_CAPTCHA_VALUE
            and captcha_value == settings.MASTER_CAPTCHA_VALUE
        ):
            CaptchaStore.objects.filter(hashkey=captcha_key).delete()
            return attrs

        try:
            store = CaptchaStore.objects.get(
                hashkey=captcha_key,
                response__iexact=captcha_value,
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
            CommentAttachment.objects.select_for_update().filter(
                id__in=[att.id for att in attachment_ids]
            ).update(comment=comment)

        return comment

    def to_representation(self, instance):
        # Ensure the new instance has the attributes expected by the DetailSerializer
        instance.is_liked = False
        instance.is_disliked = False
        instance.like_count = 0
        instance.dislike_count = 0
        return CommentDetailSerializer(instance, context=self.context).data
