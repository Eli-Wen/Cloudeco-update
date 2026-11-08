"""Structured application logs and bounded Prometheus metrics."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from prometheus_client import Counter, Histogram


class JsonFormatter(logging.Formatter):
    """Render one application log record as one JSON line on stdout."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in ("request_id", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_application_logging() -> logging.Logger:
    """Configure CloudEco logs and leave Uvicorn's logs unchanged."""
    app_logger = logging.getLogger("cloudeco")
    if app_logger.handlers:
        return app_logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    return app_logger


logger = configure_application_logging()

HTTP_REQUESTS_TOTAL = Counter(
    "cloudeco_http_requests_total",
    "Completed HTTP requests for the CloudEco API.",
    ["method", "path", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "cloudeco_http_request_duration_seconds",
    "End-to-end HTTP request duration for the CloudEco API.",
    ["method", "path"],
)
INFERENCE_DURATION_SECONDS = Histogram(
    "cloudeco_inference_duration_seconds",
    "YOLO inference duration reported by the model.",
    ["stage"],
)


def record_http_request(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Record bounded labels for Prometheus and one correlation-ready log line."""
    HTTP_REQUESTS_TOTAL.labels(method=method, path=path, status_code=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration_ms / 1000)
    logger.info(
        "HTTP request completed",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )


def record_inference_timings(*, preprocess_ms: float, inference_ms: float, postprocess_ms: float) -> None:
    """Record model timing stages without unbounded metric labels."""
    INFERENCE_DURATION_SECONDS.labels(stage="preprocess").observe(preprocess_ms / 1000)
    INFERENCE_DURATION_SECONDS.labels(stage="inference").observe(inference_ms / 1000)
    INFERENCE_DURATION_SECONDS.labels(stage="postprocess").observe(postprocess_ms / 1000)
