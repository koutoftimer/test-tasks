from django.contrib import admin

from .models import CommentAttachment


class CommentAttachmentInline(admin.TabularInline):
    model = CommentAttachment
    extra = 0


@admin.register(CommentAttachment)
class CommentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "comment", "file", "file_type")
