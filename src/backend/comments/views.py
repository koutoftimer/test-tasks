from typing import Iterable

from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from rest_framework import mixins, viewsets, filters
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from likes.models import CommentVote
from likes.redis_service import (
    attach_votes_from_redis,
    get_vote_counts,
    get_user_votes,
    sync_vote,
)
from likes.serializers import CreateVoteSerializer
from .models import Comment, sanitize_text
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentListSerializer,
)
from .utils import silk_profiler


class CommentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    http_method_names = ["get", "post", "delete", "head", "options"]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["author_username", "author_email", "id"]
    ordering = "-id"
    queryset = Comment.objects.filter(parent=None)

    def list(self, request, *args, **kwargs):
        base_qs = self.filter_queryset(self.get_queryset().only("id"))
        ordering = base_qs.query.order_by or ("-id",)
        page = self.paginate_queryset(base_qs)

        if page is not None:
            paged_ids = [c.id for c in page]

            final_qs = (
                Comment.objects.filter(id__in=paged_ids)
                .select_related("profile__user")
                .annotate(
                    reply_count=Count("replies"),
                )
                .order_by(*ordering)
            )

            serializer = self.get_serializer(final_qs, many=True)
            return self.get_paginated_response(serializer.data)

        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == "create":
            return CommentCreateSerializer
        if self.action == "replies":
            return CommentDetailSerializer
        return CommentListSerializer

    def _attach_votes_from_redis(self, comments: Iterable[Comment]):
        attach_votes_from_redis(
            comments=comments,
            user_id=(
                self.request.user.pk
                if self.request.user and self.request.user.is_authenticated
                else None
            ),
        )

    def get_serializer(self, *args, **kwargs):
        """
        Custom hook to attach Redis data just before the objects are serialized.
        This handles list, retrieve, and custom actions automatically.
        """
        if args and self.action != "create":
            instances = args[0]
            if isinstance(instances, Iterable):
                self._attach_votes_from_redis(instances)
            else:
                self._attach_votes_from_redis([instances])

        return super().get_serializer(*args, **kwargs)

    @action(detail=True, methods=["get"])
    def replies(self, request, pk):
        with silk_profiler(name="Total"):
            with silk_profiler(name="Ensure comment exists"):
                if not Comment.objects.filter(pk=pk).exists():
                    raise Http404()

            descendant_ids = Comment.get_descendant_ids(pk)

            with silk_profiler(name="Collecting nodes"):
                all_nodes = (
                    Comment.objects.filter(id__in=descendant_ids)
                    .select_related("profile__user")
                    .all()
                )

            self._attach_votes_from_redis(all_nodes)

            with silk_profiler(name="Restoring registry"):
                registry = {}
                for node in all_nodes:
                    registry.setdefault(node.parent_id, []).append(node)

            with silk_profiler(name="Serializing"):
                serializer = self.get_serializer(
                    registry.get(int(pk), []),  # Top level children
                    many=True,
                    context={**self.get_serializer_context(), "registry": registry},
                )

            with silk_profiler(name="Returning response"):
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

        new_vote = None if vote_type is None else vote_type == "like"
        sync_vote(request.user.id, comment.pk, new_vote)

        like_count, dislike_count = get_vote_counts(comment.pk)
        user_votes = get_user_votes(request.user.id, [comment.pk])
        user_vote = user_votes.get(comment.pk)

        return Response(
            {
                "vote": vote_type,
                "like_count": like_count,
                "dislike_count": dislike_count,
                "is_liked": user_vote == 1,
                "is_disliked": user_vote == -1,
            }
        )


@api_view(["POST"])
def sanitize(request):
    return Response({"text": sanitize_text(request.data.get("text", ""))})


@api_view(["GET"])
def captcha(request):
    new_key = CaptchaStore.generate_key()
    image_url = captcha_image_url(new_key)
    return Response(
        {
            "key": new_key,
            "image_url": image_url,
        }
    )
