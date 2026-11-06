"""Locust caller for the CloudEco prediction endpoint."""

import base64
import os
from pathlib import Path
from uuid import uuid4

from locust import HttpUser, between, task

DEFAULT_IMAGE_PATH = Path(__file__).resolve().parent.parent / "test_assets" / "image0.jpeg"
IMAGE_PATH = Path(os.environ.get("CLOUDECO_TEST_IMAGE", DEFAULT_IMAGE_PATH))


def load_image_as_base64() -> str:
    if not IMAGE_PATH.is_file():
        raise FileNotFoundError(f"Locust test image is missing: {IMAGE_PATH}")
    return base64.b64encode(IMAGE_PATH.read_bytes()).decode("utf-8")


class ImageApiUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self) -> None:
        self.image_base64 = load_image_as_base64()

    def request_payload(self) -> dict[str, str]:
        return {
            "uuid": str(uuid4()),
            "image": self.image_base64,
        }


class PredictionUser(ImageApiUser):

    @task
    def predict(self) -> None:
        payload = self.request_payload()
        with self.client.post(
            "/api/predict",
            json=payload,
            name="POST /api/predict",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return

            body = response.json()
            if body.get("uuid") != payload["uuid"]:
                response.failure("Response uuid does not match the request")
            elif not isinstance(body.get("boxes"), list):
                response.failure("Response boxes is not a list")
            else:
                response.success()


class AnnotationUser(ImageApiUser):

    @task
    def annotate(self) -> None:
        payload = self.request_payload()
        with self.client.post(
            "/api/annotate",
            json=payload,
            name="POST /api/annotate",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Unexpected status: {response.status_code}")
                return

            body = response.json()
            if body.get("uuid") != payload["uuid"]:
                response.failure("Response uuid does not match the request")
            elif not isinstance(body.get("image"), str) or not body["image"]:
                response.failure("Response image is missing")
            else:
                response.success()
