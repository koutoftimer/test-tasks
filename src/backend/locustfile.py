import csv
import os
import random

from faker import Faker
from locust import HttpUser, task, between

# Load the exported users into a global list
users_pool = []
with open("locust_users.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        users_pool.append(row)

fake = Faker()


MASTER_CAPTCHA_VALUE = os.environ.get(
    "MASTER_CAPTCHA_VALUE",
    "BqaCCGFi6X9MO0O0IMx2tEKaNKJ6sP_qjNTeWIQBg_mY",
)


class CommentUser(HttpUser):
    wait_time = between(1, 5)

    def on_start(self):
        # Pick a unique user from the pool for this virtual user
        self.user_data = random.choice(users_pool)
        # Login and get JWT
        res = self.client.post(
            "/api/auth/jwt/create/",
            json={
                "username": self.user_data["username"],
                "password": self.user_data["password"],
            },
        )
        self.token = res.json().get("access")
        # Get number of pages
        self.num_pages = self.client.get(f"/api/comments/").json()["count"] // 25

        page = random.randint(1, self.num_pages)
        ids = self.client.get(f"/api/comments/?page={page}").json()["results"]
        ids = [i["id"] for i in ids]
        self.random_comments = ids

    @task(3)
    def view_comments(self):
        page = random.randint(1, self.num_pages)
        self.client.get(f"/api/comments/?page={page}")

    @task(5)
    def view_comment_details(self):
        comment_id = random.choice(self.random_comments)
        self.client.get(f"/api/comments/{comment_id}/")
        self.client.get(f"/api/comments/{comment_id}/replies")

    @task(1)
    def post_comment(self):
        response = self.client.get("/api/captcha/")
        if response.status_code != 200:
            raise ValueError(response.text)
        captcha = response.json()
        payload = {
            "text": "<br>".join(fake.paragraphs(nb=random.randint(1, 5))),
            "captcha_key": captcha["key"],
            "captcha_value": MASTER_CAPTCHA_VALUE,
        }
        response = self.client.post(
            "/api/comments/",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        if response.status_code != 201:
            raise ValueError(response.text)

    @task(2)
    def vote_on_comment(self):
        comment_id = random.randint(1, 1000000)
        self.client.post(
            f"/api/comments/{comment_id}/vote/",
            json={"vote": random.choice(["like", "dislike"])},
            headers={"Authorization": f"Bearer {self.token}"},
        )
