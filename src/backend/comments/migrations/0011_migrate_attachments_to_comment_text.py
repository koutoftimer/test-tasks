from urllib.parse import urljoin

from django.conf import settings
from django.db import migrations


def migrate_attachments_to_comment_text(apps, schema_editor):
    CommentAttachment = apps.get_model("comments", "CommentAttachment")
    Comment = apps.get_model("comments", "Comment")
    base = settings.API_BASE_URL

    comment_ids = (
        CommentAttachment.objects.filter(comment__isnull=False)
        .values_list("comment_id", flat=True)
        .order_by()
        .distinct()
    )

    for cid in comment_ids:
        attachments = CommentAttachment.objects.filter(comment_id=cid)
        tags = []
        for att in attachments:
            if not att.file:
                continue
            url = urljoin(base + "/", att.file.url)
            if att.file_type == "image":
                tags.append(f'<img src="{url}">')
            elif att.file_type == "text":
                tags.append(f'<a href="{url}">Download</a>')

        if not tags:
            continue

        comment = Comment.objects.get(pk=cid)
        html = "<br>".join(tags)
        comment.text = (comment.text + "<br>" + html) if comment.text else html
        comment.save(update_fields=["text"])


class Migration(migrations.Migration):
    dependencies = [("comments", "0010_commentattachment_uploaded_at_and_more")]
    operations = [
        migrations.RunPython(
            migrate_attachments_to_comment_text,
            migrations.RunPython.noop,
        ),
    ]
