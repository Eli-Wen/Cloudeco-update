"""FastAPI entry point for wildfire and smoke inference."""

from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.model_runner import (
    InvalidImageError,
    decode_base64_image,
    encode_image_to_base64,
    model_runner,
)
from app.observability import logger, record_http_request, record_inference_timings
from app.schemas import AnnotateResponse, HealthResponse, PredictRequest, PredictResponse


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Loading YOLO model from %s", model_runner.model_path)
    model_runner.load()
    logger.info("YOLO model loaded")
    yield


app = FastAPI(title="CloudEco Wildfire Detection API", lifespan=lifespan)


@app.middleware("http")
async def observe_request(request: Request, call_next):
    """Attach a correlation ID and observe completed API requests."""
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    started_at = perf_counter()
    response = await call_next(request)
    duration_ms = (perf_counter() - started_at) * 1000

    response.headers["X-Request-ID"] = request_id
    if request.url.path != "/metrics":
        record_http_request(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
    return response


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "CloudEco API is running"}


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    if not model_runner.is_loaded:
        raise HTTPException(status_code=503, detail="model is not ready")
    return HealthResponse(status="ok", model_loaded=True)


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Expose Prometheus-format metrics for future cluster scraping."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    try:
        image = decode_base64_image(request.image)
        result = model_runner.predict_from_array(image)
    except InvalidImageError as error:
        raise HTTPException(status_code=400, detail="invalid image payload") from error
    except Exception as error:
        logger.exception("Prediction failed")
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

    speed_preprocess_ms = float(result.speed.get("preprocess", 0.0))
    speed_inference_ms = float(result.speed.get("inference", 0.0))
    speed_postprocess_ms = float(result.speed.get("postprocess", 0.0))
    record_inference_timings(
        route="/api/predict",
        preprocess_ms=speed_preprocess_ms,
        inference_ms=speed_inference_ms,
        postprocess_ms=speed_postprocess_ms,
    )

    return PredictResponse(
        uuid=request.uuid,
        count=len(detections),
        detections=detections,
        boxes=boxes,
        speed_preprocess_ms=speed_preprocess_ms,
        speed_inference_ms=speed_inference_ms,
        speed_postprocess_ms=speed_postprocess_ms,
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
        logger.exception("Annotation failed")
        raise HTTPException(status_code=500, detail="annotation failed") from error

    record_inference_timings(
        route="/api/annotate",
        preprocess_ms=float(result.speed.get("preprocess", 0.0)),
        inference_ms=float(result.speed.get("inference", 0.0)),
        postprocess_ms=float(result.speed.get("postprocess", 0.0)),
    )

    return AnnotateResponse(uuid=request.uuid, image=annotated_base64)
