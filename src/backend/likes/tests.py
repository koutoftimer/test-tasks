from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from rest_framework.test import APIClient

from comments.models import Comment
from likes.redis_service import get_redis


class TestVote(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="voter", email="voter@example.com", password="pass"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="pass"
        )
        self.comment = Comment.objects.create(text="Test comment")

    def tearDown(self):
        try:
            get_redis().flushdb()
        except Exception:
            pass

    def _auth(self, username: str = "voter", password: str = "pass") -> dict[str, str]:
        response = self.client.post(
            reverse("jwt-create"),
            data={"username": username, "password": password},
        )
        return response.json()

    def _header(self, tokens: dict[str, str]) -> dict[str, str]:
        return {"Authorization": f"Bearer {tokens['access']}"}

    def _vote_url(self, comment_id: int | None = None) -> str:
        return reverse("comment-vote", args=[comment_id or self.comment.id])

    def test_unauthenticated_cannot_vote(self):
        """POST or DELETE without JWT token returns 401."""
        url = self._vote_url()
        response = self.client.post(url, {"vote": "like"})
        self.assertEqual(response.status_code, 401)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_like_comment(self):
        """POST vote=like returns 200 and counts (1, 0)."""
        tokens = self._auth()
        response = self.client.post(
            self._vote_url(), {"vote": "like"}, headers=self._header(tokens)
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vote"], "like")
        self.assertEqual(data["like_count"], 1)
        self.assertEqual(data["dislike_count"], 0)

    def test_dislike_comment(self):
        """POST vote=dislike returns 200 and counts (0, 1)."""
        tokens = self._auth()
        response = self.client.post(
            self._vote_url(), {"vote": "dislike"}, headers=self._header(tokens)
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vote"], "dislike")
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(data["dislike_count"], 1)

    def test_change_vote(self):
        """Switching from like to dislike returns 200, vote=dislike, counts (0, 1)."""
        tokens = self._auth()
        headers = self._header(tokens)
        url = self._vote_url()

        self.client.post(url, {"vote": "like"}, headers=headers)
        response = self.client.post(url, {"vote": "dislike"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vote"], "dislike")
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(data["dislike_count"], 1)

    def test_change_vote_dislike_to_like(self):
        """Switching from dislike to like returns 200, vote=like, counts (1, 0)."""
        tokens = self._auth()
        headers = self._header(tokens)
        url = self._vote_url()

        self.client.post(url, {"vote": "dislike"}, headers=headers)
        response = self.client.post(url, {"vote": "like"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vote"], "like")
        self.assertEqual(data["like_count"], 1)
        self.assertEqual(data["dislike_count"], 0)

    def test_remove_vote(self):
        """DELETE after like returns 200, vote=None, counts reset to (0, 0)."""
        tokens = self._auth()
        headers = self._header(tokens)
        url = self._vote_url()

        self.client.post(url, {"vote": "like"}, headers=headers)
        response = self.client.delete(url, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["vote"])
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(data["dislike_count"], 0)

    def test_remove_vote_dislike(self):
        """DELETE after dislike returns 200, vote=None, counts reset to (0, 0)."""
        tokens = self._auth()
        headers = self._header(tokens)
        url = self._vote_url()

        self.client.post(url, {"vote": "dislike"}, headers=headers)
        response = self.client.delete(url, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["vote"])
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(data["dislike_count"], 0)

    def test_remove_nonexistent_vote(self):
        """DELETE without an existing vote returns 404."""
        tokens = self._auth()
        response = self.client.delete(self._vote_url(), headers=self._header(tokens))
        self.assertEqual(response.status_code, 404)

    def test_invalid_vote_type(self):
        """POST with vote=invalid returns 400."""
        tokens = self._auth()
        response = self.client.post(
            self._vote_url(),
            {"vote": "invalid"},
            headers=self._header(tokens),
        )
        self.assertEqual(response.status_code, 400)

    def test_vote_nonexistent_comment(self):
        """POST vote on a non-existent comment returns 404."""
        tokens = self._auth()
        url = self._vote_url(comment_id=99999)
        response = self.client.post(url, {"vote": "like"}, headers=self._header(tokens))
        self.assertEqual(response.status_code, 404)

    def test_vote_reply_comment(self):
        """Posts and deletes vote on a reply comment (was 404 due to get_queryset filter)."""
        reply = Comment.objects.create(text="Reply comment", parent=self.comment)
        tokens = self._auth()
        headers = self._header(tokens)
        url = self._vote_url(comment_id=reply.id)

        response = self.client.post(url, {"vote": "like"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["vote"], "like")
        self.assertEqual(data["like_count"], 1)
        self.assertEqual(data["dislike_count"], 0)

        response = self.client.delete(url, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["vote"])

    def test_counts_in_comment_list(self):
        """Like and dislike counts can reach >1 in GET /api/comments/ response."""
        headers = self._header(self._auth())

        self.client.post(self._vote_url(), {"vote": "like"}, headers=headers)

        other_headers = self._header(self._auth("other"))
        self.client.post(self._vote_url(), {"vote": "like"}, headers=other_headers)

        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertEqual(comment_data["like_count"], 2)
        self.assertEqual(comment_data["dislike_count"], 0)

        self.client.post(self._vote_url(), {"vote": "dislike"}, headers=other_headers)

        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertEqual(comment_data["like_count"], 1)
        self.assertEqual(comment_data["dislike_count"], 1)

        self.client.post(self._vote_url(), {"vote": "dislike"}, headers=headers)

        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertEqual(comment_data["like_count"], 0)
        self.assertEqual(comment_data["dislike_count"], 2)

    def test_is_liked_annotation(self):
        """is_liked=True when user likes; resets to False after DELETE."""
        tokens = self._auth()
        headers = self._header(tokens)

        self.client.post(self._vote_url(), {"vote": "like"}, headers=headers)

        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertTrue(comment_data["is_liked"])
        self.assertFalse(comment_data["is_disliked"])

        self.client.delete(self._vote_url(), headers=headers)
        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertFalse(comment_data["is_liked"])
        self.assertFalse(comment_data["is_disliked"])

    def test_is_disliked_annotation(self):
        """is_disliked=True when user dislikes; resets to False after DELETE."""
        tokens = self._auth()
        headers = self._header(tokens)

        self.client.post(self._vote_url(), {"vote": "dislike"}, headers=headers)

        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertFalse(comment_data["is_liked"])
        self.assertTrue(comment_data["is_disliked"])

        self.client.delete(self._vote_url(), headers=headers)
        response = self.client.get(reverse("comment-list"), headers=headers)
        comment_data = response.json()["results"][0]
        self.assertFalse(comment_data["is_liked"])
        self.assertFalse(comment_data["is_disliked"])

    def test_annotations_require_auth(self):
        """is_liked/is_disliked default to False for unauthenticated requests."""
        tokens = self._auth()
        self.client.post(
            self._vote_url(), {"vote": "like"}, headers=self._header(tokens)
        )

        self.client.post(
            self._vote_url(),
            {"vote": "dislike"},
            headers=self._header(self._auth("other")),
        )

        response = self.client.get(reverse("comment-list"))
        comment_data = response.json()["results"][0]
        self.assertFalse(comment_data["is_liked"])
        self.assertFalse(comment_data["is_disliked"])
