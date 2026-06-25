from django.contrib import admin

from .models import CommentVote


@admin.register(CommentVote)
class CommentVoteAdmin(admin.ModelAdmin):
    list_display = ("comment", "user", "vote")
