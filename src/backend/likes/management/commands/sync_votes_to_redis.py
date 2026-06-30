import logging
import time

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from likes.models import CommentVote
from likes.redis_service import RedisKeys, get_redis

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate Redis vote aggregations from Postgres"

    def handle(self, *args, **kwargs):
        start = time.monotonic()
        r = get_redis()

        logger.info("Clearing existing vote keys from Redis...")
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor, match="v:*", count=1000)
            if keys:
                r.delete(*keys)
            if cursor == 0:
                break

        logger.info("Aggregating vote counts per comment...")

        qs = (
            CommentVote.objects.filter(vote__isnull=False)
            .values("comment_id")
            .annotate(
                likes=Count("id", filter=Q(vote=True)),
                dislikes=Count("id", filter=Q(vote=False)),
            )
            .iterator(chunk_size=10_000)
        )

        pipe = r.pipeline(transaction=False)

        count = 0
        for count, row in enumerate(qs, 1):
            cid = row["comment_id"]
            like_field, dislike_field = RedisKeys.vote_fields(cid)
            pipe.hset(RedisKeys.VOTES_COUNTS, like_field, row["likes"])
            pipe.hset(RedisKeys.VOTES_COUNTS, dislike_field, row["dislikes"])
            if count % 1000 == 0:
                pipe.execute()
        pipe.execute()

        logger.info("Total: %s comment counts.", count)

        logger.info("Processing user votes...")

        user_votes = (
            CommentVote.objects.filter(vote__isnull=False)
            .values("user_id", "comment_id", "vote")
            .order_by("user_id")
            .iterator(chunk_size=10000)
        )

        count = 0
        for count, row in enumerate(user_votes, 1):
            pipe.hset(
                RedisKeys.user_votes(row["user_id"]),
                str(row["comment_id"]),
                "1" if row["vote"] else "-1",
            )
            if count % 1000 == 0:
                pipe.execute()
        pipe.execute()

        logger.info("Total: %s user vote records.", count)

        elapsed = time.monotonic() - start
        logger.info("Redis vote sync complete in %.2fs", elapsed)
