from django.conf import settings
from django.db import models


class CommentVote(models.Model):
    """Vote can be in one of three states:
    1. like - when vote is True
    2. dislike - when vote is False
    3. reset - when vote is None (niether like nor dislike)

    We are restrained from removing CommentVote instances because delete
    operation is more expensive in comparison to update.
    """

    comment = models.ForeignKey(
        "comments.Comment", on_delete=models.CASCADE, related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comment_votes"
    )
    vote = models.BooleanField(null=True)

    class Meta:
        app_label = "comments"
        verbose_name = "Comment Vote"
        verbose_name_plural = "Comment Votes"
        constraints = [
            models.UniqueConstraint(
                fields=("comment", "user"),
                name="vote_unique_user_comment",
                violation_error_message="You can change your vote, not vote twice.",
            )
        ]
        indexes = [
            models.Index(fields=["comment", "user", "vote"]),
        ]

    def __str__(self):
        status = (
            "like"
            if self.vote is True
            else "dislike" if self.vote is False else "removed"
        )
        return f"{status} by {self.user.username} on Comment #{self.comment_id}"
