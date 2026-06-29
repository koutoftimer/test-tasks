import csv
import os
import random

from locust import HttpUser, task, between

# Load the exported users into a global list
users_pool = []
with open("locust_users.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        users_pool.append(row)


MASTER_CAPTCHA_VALUE = os.environ.get("MASTER_CAPTCHA_VALUE", "super-secret-value")


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

    @task(3)
    def view_comments(self):
        page = random.randint(1, self.num_pages)
        self.client.get(f"/api/comments/?page={page}")

    @task(1)
    def post_comment(self):
        captcha = self.client.get("/api/captcha/").json()
        payload = {
            "text": "This is a performance test comment",
            "captcha_key": captcha["key"],
            "captcha_value": MASTER_CAPTCHA_VALUE,
        }
        self.client.post(
            "/api/comments/",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @task(2)
    def vote_on_comment(self):
        # Pick a random comment ID (e.g., between 1 and 1,000,000)
        comment_id = random.randint(1, 1000000)
        self.client.post(
            f"/api/comments/{comment_id}/vote/",
            json={"vote": random.choice(["like", "dislike"])},
            headers={"Authorization": f"Bearer {self.token}"},
        )
