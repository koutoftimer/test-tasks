from django.db.models import (
    BooleanField,
    Count,
    Exists,
    OuterRef,
    Value,
    Subquery,
    IntegerField,
)
from django.db.models.functions import Coalesce
from django.http import Http404
from django.shortcuts import get_object_or_404

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from rest_framework import viewsets, mixins
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from likes.serializers import CreateVoteSerializer
from likes.models import CommentVote
from .models import Comment, sanitize_text
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentListSerializer,
)


class CommentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "delete", "head", "options"]

    def _get_current_user(self):
        user = self.request.user
        if user.is_authenticated:
            return user
        return None

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        if self.action == "replies":
            return CommentDetailSerializer
        return CommentListSerializer

    def _annotate_votes(self, qs):
        user = self._get_current_user()
        if user:
            user_votes = CommentVote.objects.filter(comment=OuterRef("pk"), user=user)
            qs = qs.annotate(
                is_liked=Exists(user_votes.filter(vote=True)),
                is_disliked=Exists(user_votes.filter(vote=False)),
            )
        else:
            qs = qs.annotate(
                is_liked=Value(False, output_field=BooleanField()),
                is_disliked=Value(False, output_field=BooleanField()),
            )

        likes_subquery = (
            CommentVote.objects.filter(comment=OuterRef("pk"), vote=True)
            .values("comment")
            .annotate(count=Count("id"))
            .values("count")
        )
        dislikes_subquery = (
            CommentVote.objects.filter(comment=OuterRef("pk"), vote=False)
            .values("comment")
            .annotate(count=Count("id"))
            .values("count")
        )

        return qs.annotate(
            # Coalesce ensures we get 0 instead of None if no votes exist
            like_count=Coalesce(
                Subquery(likes_subquery, output_field=IntegerField()), 0
            ),
            dislike_count=Coalesce(
                Subquery(dislikes_subquery, output_field=IntegerField()), 0
            ),
        )

    def get_queryset(self):
        qs = Comment.objects.filter(parent=None).select_related("profile__user")
        qs = self._annotate_votes(qs)
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

    @action(detail=True, methods=["get"])
    def replies(self, request, pk=None):
        comment = get_object_or_404(Comment, pk=pk)

        replies = comment.replies.all().select_related("profile__user").order_by("id")
        replies = self._annotate_votes(replies)

        serializer = self.get_serializer(replies, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def vote(self, request, pk=None):
        comment = get_object_or_404(Comment, pk=pk)

        if request.method == "DELETE":
            if not CommentVote.objects.filter(
                comment=comment, user=request.user
            ).update(vote=None):
                raise Http404()
            vote_type = None
        else:
            serializer = CreateVoteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            vote_type = serializer.validated_data["vote"]

            CommentVote.objects.update_or_create(
                comment=comment,
                user=request.user,
                defaults={"vote": vote_type == "like"},
            )

        instance = self._annotate_votes(Comment.objects.filter(pk=pk)).get()

        return Response(
            {
                "vote": vote_type,
                "like_count": instance.like_count,
                "dislike_count": instance.dislike_count,
                "is_liked": instance.is_liked,
                "is_disliked": instance.is_disliked,
            }
        )


@api_view(["POST"])
def sanitize(request):
    return Response({"text": sanitize_text(request.data.get("text", ""))})


@api_view(["GET"])
def captcha(request):
    # TODO: clean up stale captchas in periodic Celery task
    new_key = CaptchaStore.generate_key()
    image_url = captcha_image_url(new_key)
    return Response(
        {
            "key": new_key,
            "image_url": image_url,
        }
    )
