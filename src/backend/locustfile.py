import csv
import os
import random
from typing import Literal, Mapping

from faker import Faker
from locust import HttpUser, task, between

# Load the exported users into a global list
users_pool = list[Mapping[Literal["username", "password"], str]]()
try:
    with open("locust_users.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users_pool.append(row)
except FileNotFoundError:
    print("Warning: locust_users.csv not found.")

random.shuffle(users_pool)
users_pool_iter = iter(users_pool)

fake = Faker()

MASTER_CAPTCHA_VALUE = os.environ.get(
    "MASTER_CAPTCHA_VALUE",
    "BqaCCGFi6X9MO0O0IMx2tEKaNKJ6sP_qjNTeWIQBg_mY",
)


class CommentUser(HttpUser):
    wait_time = between(5, 15)

    TOTAL_PAGES: int | None = None

    def get_headers(self, extension: dict[str, str] | None = None) -> dict[str, str]:
        result = {"Accept": "application/json"}
        if extension is not None:
            result.update(extension)
        return result

    def get_random_ordering(self) -> str:
        ordering = random.choice(["id", "author_username", "author_email"])
        if random.random() < 0.5:
            ordering = f"-{ordering}"
        return ordering

    @property
    def num_pages(self) -> int:
        """Cache total number of pages of comments"""
        if self.__class__.TOTAL_PAGES is not None:
            return self.__class__.TOTAL_PAGES

        res = self.client.get(
            "/api/comments/",
            name="get page count",
            headers=self.get_headers(),
        )

        if res.status_code == 200:
            self.__class__.TOTAL_PAGES = max(1, res.json()["count"] // 25)

        # if response already failed, it logs an error in the log
        elif not self.stop():
            self.stop(True)

        return self.__class__.TOTAL_PAGES

    def on_start(self):
        self.user_data = next(users_pool_iter)
        print(f"Loaded user {self.user_data}")

        # login
        request = self.client.post(
            "/api/auth/jwt/create/",
            json={
                "username": self.user_data["username"],
                "password": self.user_data["password"],
            },
            headers=self.get_headers(),
        )
        if request.status_code != 200:
            print(f"Failed to create JWT {request.status_code=} {request.text=}")
            self.stop()
            raise Exception("Login failed")

        self.tokens: dict[Literal["access", "refresh"], str] = request.json()

        import uuid

        self.id = uuid.uuid4()

        # Populate initial random comments cache
        page = random.randint(1, self.num_pages)
        res = self.client.get(
            f"/api/comments/?page={page}",
            name="populate self.random_comments",
            headers=self.get_headers(),
        )
        if res.status_code == 200:
            self.random_comments = [i["id"] for i in res.json()["results"]]

    def post_with_auth(self, url, payload, name=None):
        """Helper to handle token expiration by re-logging once on 401."""
        headers = self.get_headers({"Authorization": f"Bearer {self.tokens['access']}"})
        # main request may fail with 401 when token expires
        with self.client.post(
            url,
            json=payload,
            headers=headers,
            name=name,
            catch_response=True,
        ) as original:
            # we are interested only in token expiration
            if original.status_code != 401 or "token_not_valid" not in original.text:
                return

            # refresh request have to always succeed
            auth = self.client.post(
                "/api/auth/jwt/refresh/",
                json={"refresh": self.tokens["refresh"]},
                headers=self.get_headers(),
            )
            if "token_not_valid" not in auth.text:
                try:
                    self.tokens["access"] = auth.json()["access"]
                except Exception as e:
                    original.failure("Failed to load refresh token")
                    self.stop()
            else:
                print(f"2. Token not valid. WTF? {self.id}: {auth.json()=}")
                self.stop()
                original.failure("Failed to load refresh token: token not valid")

            headers = self.get_headers(
                {"Authorization": f"Bearer {self.tokens['access']}"}
            )
            repeated = self.client.post(
                url,
                json=payload,
                headers=headers,
                name=name,
            )

            # mark request failed by token expiration as successful after refreshing token
            if 200 <= repeated.status_code < 300:
                original.success()

    @task(3)
    def view_comments(self):
        page = random.randint(1, self.num_pages)
        ordering = self.get_random_ordering()
        self.client.get(
            f"/api/comments/?page={page}&ordering={ordering}",
            headers=self.get_headers(),
            name="list comments on random page with random ordering",
        )

    @task(5)
    def view_comment_details(self):
        if not self.random_comments:
            return
        comment_id = random.choice(self.random_comments)
        self.client.get(
            f"/api/comments/{comment_id}/",
            name="/api/comments/[id]/",
            headers=self.get_headers(),
        )
        self.client.get(
            f"/api/comments/{comment_id}/replies/",
            name="/api/comments/[id]/replies/",
            headers=self.get_headers(),
        )

    @task(1)
    def post_comment(self):
        captcha_res = self.client.get(
            "/api/captcha/",
            headers=self.get_headers(),
        )
        if captcha_res.status_code != 200:
            return

        captcha = captcha_res.json()
        payload = {
            "text": "<br>".join(fake.paragraphs(nb=random.randint(1, 5))),
            "captcha_key": captcha["key"],
            "captcha_value": MASTER_CAPTCHA_VALUE,
        }

        self.post_with_auth("/api/comments/", payload)

    @task(2)
    def vote_on_comment(self):
        if not self.random_comments:
            return
        comment_id = random.choice(self.random_comments)
        payload = {"vote": random.choice(["like", "dislike"])}

        self.post_with_auth(
            f"/api/comments/{comment_id}/vote/",
            payload,
            name="/api/comments/[id]/vote/",
        )
