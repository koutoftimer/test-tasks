from rest_framework import mixins, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from .models import CommentAttachment
from .serializers import UploadSerializer


class UploadViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = CommentAttachment.objects.all()
    serializer_class = UploadSerializer
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        # TODO: set periodic Celery task instead
        CommentAttachment.delete_orphans()
        return super().create(request, *args, **kwargs)
