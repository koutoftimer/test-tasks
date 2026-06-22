from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Comment, CommentVote, Profile
from .serializers import (
    CommentCreateSerializer,
    CommentDetailSerializer,
    CommentListSerializer,
    ProfileDetailSerializer,
    ProfileUpdateSerializer,
)


class CommentViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]

    def _get_current_user(self):
        user = self.request.user
        if user.is_authenticated:
            return user
        return None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self._get_current_user()
        context["voter"] = user
        return context

    def get_serializer_class(self):
        if self.request.method == "POST":
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
        return qs.annotate(
            like_count=Count("votes", filter=Q(votes__vote=True)),
            dislike_count=Count("votes", filter=Q(votes__vote=False)),
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
        try:
            comment = Comment.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        replies = comment.replies.all().order_by("id")
        replies = self._annotate_votes(replies)
        serializer = CommentDetailSerializer(replies, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=True, methods=["post", "delete"], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        try:
            comment = Comment.objects.get(pk=pk)
        except ObjectDoesNotExist:
            return Response({"error": "Comment not found."}, status=status.HTTP_404_NOT_FOUND)
        user = request.user

        if request.method == "DELETE":
            updated = CommentVote.objects.filter(
                comment=comment, user=user
            ).update(vote=None)
            if not updated:
                return Response(
                    {"error": "Vote not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            like_count = comment.votes.filter(vote=True).count()
            dislike_count = comment.votes.filter(vote=False).count()
            return Response(
                {"vote": None, "like_count": like_count, "dislike_count": dislike_count}
            )

        vote_type = request.data.get("vote")
        if vote_type not in ("like", "dislike"):
            return Response(
                {"error": 'vote must be "like" or "dislike".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vote_val = True if vote_type == "like" else False
        CommentVote.objects.update_or_create(
            comment=comment,
            user=user,
            defaults={"vote": vote_val},
        )

        like_count = comment.votes.filter(vote=True).count()
        dislike_count = comment.votes.filter(vote=False).count()
        return Response(
            {"vote": vote_type, "like_count": like_count, "dislike_count": dislike_count}
        )


@api_view(["GET"])
def captcha(request):
    new_key = CaptchaStore.generate_key()
    image_url = captcha_image_url(new_key)
    return Response({
        "key": new_key,
        "image_url": image_url,
    })


class ProfileViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Profile.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileDetailSerializer

    def partial_update(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProfileDetailSerializer(profile).data)
