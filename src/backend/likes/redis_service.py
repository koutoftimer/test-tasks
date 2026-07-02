"""
Redis schema

Key             Type    Fields                          Meaning
"v:c"           HASH    {comment_id}:l, {comment_id}:d  Total likes/dislikes for comment_id
"v:u:{user_id}" HASH    {comment_id}                    1=liked, -1=disliked, absent=neutral

"v:c" — single hash map for all comment count aggregations
"v:u:{user_id}" — stores per-user vote state
"""

import pathlib
from typing import Iterable

from django.conf import settings

import redis

from comments.models import Comment
from comments.utils import silk_profiler

_SYNC_SCRIPT = pathlib.Path(__file__).parent.joinpath("sync_script.lua").read_text()


class RedisKeys:
    """
    Namespace for Redis key and field construction.
    Using shorter names like 'v' for 'votes' to save memory.
    """

    VOTES_COUNTS = "v:c"
    """The Global Hash: Stores like/dislike counts for all comments"""

    @classmethod
    def user_votes(cls, user_id: int) -> str:
        """Hash key for a specific user's vote map."""
        return f"v:u:{user_id}"

    @staticmethod
    def vote_fields(comment_id: int) -> tuple[str, str]:
        """Field names for the VOTES_COUNTS hash: (like_field, dislike_field)"""
        return f"{comment_id}:l", f"{comment_id}:d"

    @classmethod
    def bulk_vote_fields(cls, comment_ids: list[int]) -> list[str]:
        """Generates a flat list of fields for an HMGET pipeline call.

        Returns list of keys {comment_id}:l, {comment_id}:d for each comment_id.
        """
        fields = list[str]()
        for cid in comment_ids:
            fields.extend(cls.vote_fields(cid))
        return fields


_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Singleton of redis client."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    if getattr(settings, "REDIS_FAKE", False):
        import fakeredis

        _redis_client = fakeredis.FakeStrictRedis(decode_responses=True)

    else:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    return _redis_client


def get_vote_counts(comment_id: int) -> tuple[int, int]:
    """Returns total number of likes and dislikes for given comment_id."""
    r = get_redis()
    keys = RedisKeys.vote_fields(comment_id)
    likes, dislikes = r.hmget(RedisKeys.VOTES_COUNTS, keys)
    return (int(likes or 0), int(dislikes or 0))


def get_batch_vote_counts(comment_ids: list[int]) -> dict[int, tuple[int, int]]:
    """Returns total number of likes and dislikes for each comment_id."""
    if not comment_ids:
        return {}
    r = get_redis()
    values = r.hmget(RedisKeys.VOTES_COUNTS, RedisKeys.bulk_vote_fields(comment_ids))
    it = iter(values)
    return {cid: (int(next(it) or 0), int(next(it) or 0)) for cid in comment_ids}


def get_user_votes(user_id: int, comment_ids: list[int]) -> dict[int, int]:
    """Returns user's vote state for each comment_id."""
    if not comment_ids:
        return {}
    r = get_redis()
    key = RedisKeys.user_votes(user_id)
    fields = r.hmget(key, [str(cid) for cid in comment_ids])
    return {cid: int(val) for cid, val in zip(comment_ids, fields) if val is not None}


def sync_vote(user_id: int, comment_id: int, new_vote_value: bool | None) -> None:
    vote_map = {True: "1", False: "-1", None: "0"}
    get_redis().eval(
        _SYNC_SCRIPT,
        2,
        RedisKeys.user_votes(user_id),
        RedisKeys.VOTES_COUNTS,
        str(comment_id),
        vote_map[new_vote_value],
    )


def attach_votes_from_redis(comments: Iterable[Comment], user_id: int | None):
    """Dynamically assigns new properties to provided comments inplace in order
    to annotate comments with `like_count`, `dislike_count`, `is_liked` and
    `is_disliked`.
    """
    with silk_profiler(name="Annotating comments using Redis"):
        if not comments:
            return
        comment_ids = [c.pk for c in comments]

        counts = get_batch_vote_counts(comment_ids)

        if user_id is None:
            user_votes = {}
        else:
            user_votes = get_user_votes(user_id, comment_ids)

        for comment in comments:
            cid = comment.pk
            like_count, dislike_count = counts.get(cid, (0, 0))
            comment.like_count = like_count
            comment.dislike_count = dislike_count
            user_vote = user_votes.get(cid)
            comment.is_liked = user_vote == 1
            comment.is_disliked = user_vote == -1
