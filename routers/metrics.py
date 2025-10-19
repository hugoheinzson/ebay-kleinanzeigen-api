"""Expose Prometheus metrics for the API and background services."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["monitoring"])


@router.get("/metrics")
async def metrics() -> Response:
    """Return the Prometheus metrics registry."""

    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
