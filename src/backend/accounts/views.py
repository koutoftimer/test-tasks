from rest_framework import mixins, viewsets

from .models import Profile
from .serializers import ProfileUpdateSerializer
from .permissions import EditPersonalProfileOnly


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Profile.objects.all()
    permission_classes = [EditPersonalProfileOnly]
    serializer_class = ProfileUpdateSerializer
