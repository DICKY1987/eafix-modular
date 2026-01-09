# DOC_ID: DOC-SERVICE-0023
from locust import HttpUser, task, between
import os


class WebsiteUser(HttpUser):
    wait_time = between(1, 2)
    target = os.getenv("TARGET_URL", "/healthz")

    @task
    def health(self):
        r = self.client.get(self.target)
        assert r.status_code == 200

