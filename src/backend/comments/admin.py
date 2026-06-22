from django.contrib import admin

from .models import Comment, CommentAttachment, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "homepage", "avatar")
    search_fields = ("user__username", "user__email")


class CommentAttachmentInline(admin.TabularInline):
    model = CommentAttachment
    extra = 0


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "text_preview", "parent", "created_at")
    list_filter = ("created_at",)
    search_fields = ("text", "profile__user__username")
    date_hierarchy = "created_at"
    inlines = [CommentAttachmentInline]

    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    text_preview.short_description = "Text"
