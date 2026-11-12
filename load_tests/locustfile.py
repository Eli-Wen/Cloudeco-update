"""Locust caller for the CloudEco prediction endpoint."""

import base64
import os
from itertools import cycle
from pathlib import Path
from uuid import uuid4

from locust import HttpUser, between, task

DEFAULT_IMAGE_DIR = Path(__file__).resolve().parent.parent / "test_assets"
IMAGE_DIR = Path(os.environ.get("CLOUDECO_TEST_IMAGE_DIR", DEFAULT_IMAGE_DIR))
TEST_IMAGE_NAMES = tuple(f"image{index}.jpeg" for index in range(10))


def load_images_as_base64() -> tuple[str, ...]:
    """Load ten fixed test images once, before Locust begins sending requests."""
    image_paths = tuple(IMAGE_DIR / name for name in TEST_IMAGE_NAMES)
    missing = [str(path) for path in image_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Locust test images are missing: {', '.join(missing)}")
    return tuple(base64.b64encode(path.read_bytes()).decode("utf-8") for path in image_paths)


class ImageApiUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self) -> None:
        self.image_base64_cycle = cycle(load_images_as_base64())

    def request_payload(self) -> dict[str, str]:
        return {
            "uuid": str(uuid4()),
            "image": next(self.image_base64_cycle),
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
