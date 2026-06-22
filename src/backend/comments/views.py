from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import Comment
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentListSerializer,
)


class CommentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "head", "options"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        if self.action == "replies":
            return CommentDetailSerializer
        return CommentListSerializer

    def get_queryset(self):
        qs = Comment.objects.filter(parent=None).select_related("profile__user")
        sort_by = self.request.query_params.get("sort", "-id")
        allowed_sorts = {
            "user_name": "profile__user__username",
            "-user_name": "-profile__user__username",
            "email": "profile__user__email",
            "-email": "-profile__user__email",
            "created_at": "id",
            "-created_at": "-id",
        }
        sort_field = allowed_sorts.get(sort_by, "-id")
        return qs.order_by(sort_field)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        pass

    @action(detail=True, methods=["get"])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.all().order_by("id")
        serializer = CommentDetailSerializer(replies, many=True, context=self.get_serializer_context())
        return Response(serializer.data)


@api_view(["GET"])
def captcha(request):
    new_key = CaptchaStore.generate_key()
    image_url = captcha_image_url(new_key)
    return Response({
        "key": new_key,
        "image_url": image_url,
    })
