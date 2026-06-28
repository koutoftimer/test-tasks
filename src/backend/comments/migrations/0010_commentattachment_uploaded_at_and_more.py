from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('comments', '0009_alter_commentattachment_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='commentattachment',
            name='uploaded_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='commentattachment',
            name='comment',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='attachments',
                to='comments.comment',
            ),
        ),
    ]
