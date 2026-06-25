from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "username", "homepage", "avatar"]


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(source="user.email")
    homepage = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    avatar = serializers.ImageField(required=False)

    def update(self, instance, validated_data):
        email = validated_data.get("user", {}).get("email")
        if email is not None:
            instance.user.email = email
            instance.user.save()

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
