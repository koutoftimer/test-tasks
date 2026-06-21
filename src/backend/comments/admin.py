from django.contrib import admin

from .models import Comment, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "homepage", "avatar")
    search_fields = ("user__username", "user__email")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "text_preview", "parent", "created_at", "file_type")
    list_filter = ("created_at", "file_type")
    search_fields = ("text", "profile__user__username")
    date_hierarchy = "created_at"

    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Text"
