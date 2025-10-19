"""API endpoints for managing scraper scheduler jobs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from schemas import (
    SchedulerJobActionResponse,
    SchedulerJobCreate,
    SchedulerJobResponse,
    SchedulerJobUpdate,
    SchedulerJobsResponse,
)
from services.scheduler import ScraperJobConfig, SchedulerJobState

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


def _get_scheduler(request: Request):
    scheduler = getattr(request.app.state, "scraper_scheduler", None)
    if scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler ist nicht verfügbar")
    return scheduler


def _state_to_response(state: SchedulerJobState) -> SchedulerJobResponse:
    params = state.params or {}
    return SchedulerJobResponse(
        id=state.id,
        name=state.name,
        interval_seconds=state.interval_seconds,
        is_active=state.is_active,
        query=params.get("query"),
        location=params.get("location"),
        radius=params.get("radius"),
        min_price=params.get("min_price"),
        max_price=params.get("max_price"),
        page_count=int(params.get("page_count") or 1),
        last_run_at=state.last_run_at,
        next_run_at=state.next_run_at,
        last_run_status=state.last_run_status,
        last_run_message=state.last_run_message,
        last_run_duration_seconds=state.last_run_duration_seconds,
        last_result_count=state.last_result_count,
        created_at=state.created_at,
        updated_at=state.updated_at,
    )


@router.get("/jobs", response_model=SchedulerJobsResponse)
async def list_jobs(request: Request) -> SchedulerJobsResponse:
    scheduler = _get_scheduler(request)
    states = await scheduler.list_jobs()
    jobs = [_state_to_response(state) for state in sorted(states, key=lambda s: s.created_at)]
    return SchedulerJobsResponse(jobs=jobs)


@router.post(
    "/jobs",
    response_model=SchedulerJobActionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_job(request: Request, payload: SchedulerJobCreate) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    config = ScraperJobConfig(
        name=payload.name,
        interval_seconds=payload.interval_seconds,
        params={
            "query": payload.query,
            "location": payload.location,
            "radius": payload.radius,
            "min_price": payload.min_price,
            "max_price": payload.max_price,
            "page_count": payload.page_count,
        },
        is_active=payload.is_active,
    )
    try:
        state = await scheduler.add_job(config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde erstellt",
    )


@router.patch("/jobs/{job_id}", response_model=SchedulerJobActionResponse)
async def update_job(request: Request, job_id: int, payload: SchedulerJobUpdate) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    update_data = payload.model_dump(exclude_unset=True)

    params = {key: update_data.pop(key) for key in list(update_data.keys()) if key in {
        "query",
        "location",
        "radius",
        "min_price",
        "max_price",
        "page_count",
    }}

    interval_seconds = update_data.get("interval_seconds")
    is_active = update_data.get("is_active")

    try:
        state = await scheduler.update_job(
            job_id,
            params=params if params else None,
            interval_seconds=interval_seconds,
            is_active=is_active,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "nicht gefunden" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde aktualisiert",
    )


@router.post("/jobs/{job_id}/start", response_model=SchedulerJobActionResponse)
async def start_job(request: Request, job_id: int) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    try:
        state = await scheduler.set_job_active(job_id, True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde gestartet",
    )


@router.post("/jobs/{job_id}/stop", response_model=SchedulerJobActionResponse)
async def stop_job(request: Request, job_id: int) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    try:
        state = await scheduler.set_job_active(job_id, False)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde gestoppt",
    )


@router.post("/jobs/{job_id}/run", response_model=SchedulerJobActionResponse)
async def run_job_now(request: Request, job_id: int) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    try:
        state = await scheduler.run_job_once(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde ausgeführt",
    )


@router.delete("/jobs/{job_id}", response_model=SchedulerJobActionResponse)
async def delete_job(request: Request, job_id: int) -> SchedulerJobActionResponse:
    scheduler = _get_scheduler(request)
    try:
        state = await scheduler.delete_job(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return SchedulerJobActionResponse(
        job=_state_to_response(state),
        message="Job wurde gelöscht",
    )
