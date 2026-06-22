import re

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import Comment, Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "username", "email", "homepage", "avatar"]


class CommentListSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

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
        ]

    def get_file(self, obj):
        if obj.file:
            return f"{settings.API_BASE_URL}{obj.file.url}"
        return None

    def get_replies(self, obj):
        replies = obj.replies.all()
        if replies:
            return CommentListSerializer(
                replies, many=True, context=self.context
            ).data
        return []


class CommentCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    homepage = serializers.URLField(required=False, allow_blank=True)
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)
    text = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)

    def validate_username(self, value):
        if not re.match(r"^[a-zA-Z0-9]+$", value):
            raise serializers.ValidationError(
                "Username must contain only Latin letters and digits."
            )
        return value

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
        if value is not None:
            try:
                Comment.objects.get(id=value)
            except Comment.DoesNotExist:
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
        username = validated_data["username"]
        email = validated_data["email"]
        homepage = validated_data.get("homepage", "")
        text = validated_data["text"]
        parent_id = validated_data.get("parent_id")
        file = validated_data.get("file")

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": email},
        )
        if user.email != email:
            user.email = email
            user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        if homepage and profile.homepage != homepage:
            profile.homepage = homepage
            profile.save()

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
        return CommentListSerializer(instance, context=self.context).data
