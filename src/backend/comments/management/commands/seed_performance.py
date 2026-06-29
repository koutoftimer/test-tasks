import random
import csv
import uuid
from urllib.parse import urljoin

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction

from faker import Faker

from accounts.models import Profile
from comments.models import Comment
from likes.models import CommentVote
from attachments.models import CommentAttachment, FileType

User = get_user_model()
fake = Faker()


def generate_comment(
    created_profiles: list[Profile],
    created_comment_ids: list[int],
) -> Comment:
    content = f"<p>{fake.paragraph()}</p>"
    parent_id = random.choice(created_comment_ids) if created_comment_ids else None
    return Comment(
        profile=random.choice(created_profiles),
        text=content,
        parent_id=parent_id,
    )


def _create_attachments(chunk_ids, image_pool, text_pool):
    selected = random.sample(chunk_ids, k=len(chunk_ids) // 5)

    attachment_objs = []
    comment_data = []
    for cid in selected:
        n_images = random.randint(1, 5)
        n_texts = random.randint(1, 5)
        imgs = random.choices(image_pool, k=n_images)
        txts = random.choices(text_pool, k=n_texts)
        comment_data.append((cid, imgs, txts))
        for path in imgs:
            attachment_objs.append(
                CommentAttachment(comment_id=cid, file=path, file_type=FileType.IMAGE)
            )
        for path in txts:
            attachment_objs.append(
                CommentAttachment(comment_id=cid, file=path, file_type=FileType.TEXT)
            )

    CommentAttachment.objects.bulk_create(attachment_objs, batch_size=5000)

    base = settings.API_BASE_URL
    comments = Comment.objects.in_bulk([cid for cid, _, _ in comment_data])
    for cid, imgs, txts in comment_data:
        tags = []
        for path in imgs:
            url = urljoin(base + "/", settings.MEDIA_URL + path)
            tags.append(f'<img src="{url}">')
        for path in txts:
            url = urljoin(base + "/", settings.MEDIA_URL + path)
            tags.append(f'<a href="{url}">Download</a>')
        html = "<br>".join(tags)
        comment = comments[cid]
        comment.text = f"{comment.text}<br>{html}"

    Comment.objects.bulk_update(comments.values(), ["text"], batch_size=5000)


class Command(BaseCommand):
    help = "Seeds 100K users and 1M comments for performance testing"

    def handle(self, *args, **kwargs):
        # 1. Validate mock data early
        mock_avatar_dir = settings.MEDIA_ROOT / "avatars" / "mock"
        avatar_paths = list(mock_avatar_dir.glob("**/*.png"))
        if not avatar_paths:
            raise CommandError(
                "No mock avatars found in MEDIA_ROOT/avatars/mock/. "
                "Populate the directory with .png files first."
            )
        avatars = [str(p.relative_to(settings.MEDIA_ROOT)) for p in avatar_paths]

        mock_upload_dir = settings.MEDIA_ROOT / "uploads" / "mock"
        image_paths = sorted(
            str(p.relative_to(settings.MEDIA_ROOT))
            for p in mock_upload_dir.glob("**/*.png")
        )
        if not image_paths:
            raise CommandError(
                "No mock images found in MEDIA_ROOT/uploads/mock/. "
                "Populate with .png files first."
            )

        self.stdout.write("Generating mock text files...")
        text_pool = []
        for _ in range(100):
            content = "\n\n".join(fake.paragraphs(nb=random.randint(3, 10)))
            name = f"uploads/mock/{uuid.uuid4().hex}.txt"
            path = default_storage.save(name, ContentFile(content))
            text_pool.append(str(path))

        # 2. Create 100K Users
        self.stdout.write("Creating 100,000 users...")
        user_list = []
        auth_data = []  # For Locust CSV

        password = make_password("password123")
        for i in range(100000):
            username = f"user_{i}"
            user_list.append(
                User(
                    username=username,
                    email=f"{username}@example.com",
                    password=password,
                )
            )
            auth_data.append([username, "password123"])

        with transaction.atomic():
            created_users = User.objects.bulk_create(user_list, batch_size=5000)
            del user_list

            profile_batch = [
                Profile(user=user, avatar=random.choice(avatars))
                for user in created_users
            ]
            created_profiles = Profile.objects.bulk_create(
                profile_batch, batch_size=5000
            )
            del profile_batch

        # 3. Create 1M Comments with attachments
        self.stdout.write("Creating 1,000,000 comments...")

        created_comment_ids: list[int] = []
        for chunk in range(20):
            comments = [
                generate_comment(created_profiles, created_comment_ids)
                for _ in range(50_000)
            ]
            created = Comment.objects.bulk_create(comments, batch_size=5000)
            chunk_ids = [c.pk for c in created]
            created_comment_ids.extend(chunk_ids)
            _create_attachments(chunk_ids, image_paths, text_pool)
            self.stdout.write(f"Chunk {chunk+1}/20 done...")

        # 4. Create 2M Votes (Random likes/dislikes)
        self.stdout.write("Creating votes...")

        comment_ids = list(Comment.objects.values_list("id", flat=True))
        for _ in range(20):
            votes = []
            for _ in range(100000):  # Just 100k for the example, adjust as needed
                votes.append(
                    CommentVote(
                        user=random.choice(created_users),
                        comment_id=random.choice(comment_ids),
                        vote=random.choice([True, False]),
                    )
                )
            CommentVote.objects.bulk_create(
                votes, ignore_conflicts=True, batch_size=5000
            )

        # 5. Export for Locust
        with open(settings.BASE_DIR / "locust_users.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["username", "password"])
            writer.writerows(auth_data)

        self.stdout.write(self.style.SUCCESS("Successfully seeded performance data!"))
