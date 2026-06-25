from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Profile
        fields = ["id", "username", "homepage", "avatar"]


class ProfileDetailSerializer(ProfileSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta(ProfileSerializer.Meta):
        fields = ProfileSerializer.Meta.fields + ["email"]


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    homepage = serializers.URLField(required=False, allow_blank=True, allow_null=True)

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
