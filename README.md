# CloudEco DevOps

CloudEco is a portfolio reconstruction of a FIT5225 coursework baseline: a FastAPI service that uses a YOLO model to detect wildfire and smoke in an image.

This repository is being rebuilt incrementally. The goal is to understand and verify each delivery step rather than copy the coursework submission.

## Current stage

Repository bootstrap. The first implementation stage is the local FastAPI inference API; Docker, Locust, Kubernetes, Azure infrastructure, CI/CD, monitoring and runbooks will be added only after their prerequisites work.

## Planned request path

```text
API caller -> localhost:8000 -> Docker port mapping -> Uvicorn/FastAPI -> YOLO model
```

The repository does not distribute model weights or credentials. See `.gitignore` for local-only material.
