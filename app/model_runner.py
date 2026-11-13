"""YOLO lifecycle and image conversion boundary for the API layer."""

import base64
import os
from threading import Lock
from pathlib import Path
from typing import Any

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "fire_m.pt"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_INFERENCE_IMAGE_SIZE = 640


def get_inference_image_size() -> int:
    """Read a validated square input size for YOLO inference."""
    raw_value = os.getenv("YOLO_INFERENCE_IMAGE_SIZE", str(DEFAULT_INFERENCE_IMAGE_SIZE))
    try:
        image_size = int(raw_value)
    except ValueError as error:
        raise ValueError("YOLO_INFERENCE_IMAGE_SIZE must be a positive integer") from error

    if image_size <= 0:
        raise ValueError("YOLO_INFERENCE_IMAGE_SIZE must be a positive integer")
    return image_size


class InvalidImageError(ValueError):
    """Raised when a caller supplies an unreadable or oversized image."""


class ModelRunner:
    """Loads one YOLO model per API process and performs inference."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        self.model_path = model_path
        self.model: Any | None = None
        self._inference_lock = Lock()

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        """Load model weights only during application startup."""
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model file is missing: {self.model_path}")

        from ultralytics import YOLO

        self.model = YOLO(str(self.model_path))

    def predict_from_array(self, image_array: np.ndarray) -> Any:
        if self.model is None:
            raise RuntimeError("Model has not been loaded")

        # Ultralytics' predictor keeps mutable request state. FastAPI runs
        # synchronous endpoints in a thread pool, so sharing it without a
        # lock can race model setup and inflate memory usage.
        with self._inference_lock:
            results = self.model(
                image_array,
                imgsz=get_inference_image_size(),
                verbose=False,
            )
        return results[0]


model_runner = ModelRunner()


def decode_base64_image(image_b64: str) -> np.ndarray:
    """Decode one base64 image without retaining caller data on disk."""
    try:
        image_bytes = base64.b64decode(image_b64, validate=True)
    except (ValueError, TypeError) as error:
        raise InvalidImageError("Image is not valid base64") from error

    if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
        raise InvalidImageError("Image payload is empty or exceeds the size limit")

    image_buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)
    if image is None:
        raise InvalidImageError("Image bytes cannot be decoded")

    return image


def encode_image_to_base64(image: np.ndarray) -> str:
    success, buffer = cv2.imencode(".jpg", image)
    if not success:
        raise RuntimeError("Annotated image encoding failed")
    return base64.b64encode(buffer.tobytes()).decode("utf-8")
