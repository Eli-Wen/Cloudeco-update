"""FastAPI entry point for wildfire and smoke inference."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.model_runner import (
    InvalidImageError,
    decode_base64_image,
    encode_image_to_base64,
    model_runner,
)
from app.schemas import AnnotateResponse, HealthResponse, PredictRequest, PredictResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Loading YOLO model from %s", model_runner.model_path)
    model_runner.load()
    logger.info("YOLO model loaded")
    yield


app = FastAPI(title="CloudEco Wildfire Detection API", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "CloudEco API is running"}


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    if not model_runner.is_loaded:
        raise HTTPException(status_code=503, detail="model is not ready")
    return HealthResponse(status="ok", model_loaded=True)


@app.post("/api/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        image = decode_base64_image(request.image)
        result = model_runner.predict_from_array(image)
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail="invalid image payload") from error
    except Exception as error:
        logger.exception("Prediction failed for request %s", request.uuid)
        raise HTTPException(status_code=500, detail="inference failed") from error

    detections: list[str] = []
    boxes: list[dict[str, float]] = []
    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append(result.names[class_id])
            boxes.append(
                {
                    "x": x1,
                    "y": y1,
                    "width": x2 - x1,
                    "height": y2 - y1,
                    "probability": confidence,
                }
            )

    return PredictResponse(
        uuid=request.uuid,
        count=len(detections),
        detections=detections,
        boxes=boxes,
        speed_preprocess_ms=float(result.speed.get("preprocess", 0.0)),
        speed_inference_ms=float(result.speed.get("inference", 0.0)),
        speed_postprocess_ms=float(result.speed.get("postprocess", 0.0)),
    )


@app.post("/api/annotate", response_model=AnnotateResponse)
def annotate(request: PredictRequest) -> AnnotateResponse:
    try:
        image = decode_base64_image(request.image)
        result = model_runner.predict_from_array(image)
        annotated_image = result.plot()
        annotated_base64 = encode_image_to_base64(annotated_image)
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail="invalid image payload") from error
    except Exception as error:
        logger.exception("Annotation failed for request %s", request.uuid)
        raise HTTPException(status_code=500, detail="annotation failed") from error

    return AnnotateResponse(uuid=request.uuid, image=annotated_base64)
