from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from .models import Comment, Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "username", "homepage", "avatar"]

class ProfileDetailSerializer(ProfileSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + ["email"]


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
            "file",
            "file_type",
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
            "file",
            "file_type",
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
    file = serializers.FileField(required=False, allow_null=True)
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Text is required.")
        return value

    def validate_file(self, value):
        if value:
            ext = value.name.split(".")[-1].lower()
            if ext in ("jpg", "jpeg", "png", "gif"):
                pass
            elif ext == "txt":
                if value.size > 100 * 1024:
                    raise serializers.ValidationError(
                        "Text file exceeds maximum size of 100KB."
                    )
            else:
                raise serializers.ValidationError(
                    "Only JPG, GIF, PNG, and TXT files are allowed."
                )
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
        text = validated_data["text"]
        parent_id = validated_data.get("parent_id")
        file = validated_data.get("file")

        request = self.context.get("request")
        profile = None
        if request and request.user.is_authenticated:
            profile, _ = Profile.objects.get_or_create(user=request.user)

        file_type = None
        if file:
            ext = file.name.split(".")[-1].lower()
            if ext in ("jpg", "jpeg", "png", "gif"):
                file_type = "image"
            elif ext == "txt":
                file_type = "text"

        parent = None
        if parent_id:
            parent = Comment.objects.get(id=parent_id)

        comment = Comment.objects.create(
            profile=profile,
            text=text,
            parent=parent,
            file=file,
            file_type=file_type,
        )

        return comment

    def to_representation(self, instance):
        return CommentDetailSerializer(instance, context=self.context).data


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    homepage = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    avatar = serializers.ImageField(required=False, allow_null=True)

    def update(self, instance, validated_data):
        user = instance.user
        email = validated_data.get("email")
        if email is not None:
            user.email = email
            user.save()

        homepage = validated_data.get("homepage")
        if homepage is not None:
            instance.homepage = homepage or None

        avatar = validated_data.get("avatar")
        if avatar is not None:
            instance.avatar = avatar

        instance.save()
        return instance


class UserSerializer(BaseUserSerializer):
    profile_id = serializers.IntegerField(source="profile.id", read_only=True)

    class Meta(BaseUserSerializer.Meta):
        fields = BaseUserSerializer.Meta.fields + ("profile_id",)
