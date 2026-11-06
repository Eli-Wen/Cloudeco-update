"""HTTP request and response contracts for the CloudEco API."""

from typing import List

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """A caller-supplied image and correlation identifier."""

    uuid: str = Field(min_length=1, max_length=128)
    image: str = Field(min_length=1, description="Base64-encoded image bytes")


class BoxItem(BaseModel):
    x: float
    y: float
    width: float
    height: float
    probability: float


class PredictResponse(BaseModel):
    uuid: str
    count: int
    detections: List[str]
    boxes: List[BoxItem]
    speed_preprocess_ms: float
    speed_inference_ms: float
    speed_postprocess_ms: float


class AnnotateResponse(BaseModel):
    uuid: str
    image: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
