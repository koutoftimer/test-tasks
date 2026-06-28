from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated, AND

from .models import Profile
from .serializers import ProfileUpdateSerializer
from .permissions import IsOwnProfile


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Profile.objects.prefetch_related("user")
    permission_classes = [IsAuthenticated & IsOwnProfile]
    serializer_class = ProfileUpdateSerializer
