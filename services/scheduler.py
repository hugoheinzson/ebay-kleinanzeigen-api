"""Background scheduler for periodic scraping jobs."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from events import ListingImagesUpdated
from repositories import ListingRepository, SchedulerJobRepository
from services.event_bus import EventBus
from services.kleinanzeigen import fetch_listings, fetch_listing_details


@dataclass(slots=True)
class ScraperJobConfig:
    """Configuration for bootstrap jobs supplied via environment variables."""

    name: str
    interval_seconds: int
    params: Dict[str, Any]
    is_active: bool = True

    @property
    def search_metadata(self) -> Dict[str, Any]:
        meta = dict(self.params)
        meta["name"] = self.name
        return meta


@dataclass(slots=True)
class SchedulerJobState:
    """Runtime state of a scheduled scraping job."""

    id: int
    name: str
    interval_seconds: int
    params: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_message: Optional[str] = None
    last_run_duration_seconds: Optional[float] = None
    last_result_count: Optional[int] = None

    @property
    def search_metadata(self) -> Dict[str, Any]:
        meta = dict(self.params)
        meta["name"] = self.name
        return meta


def _default_interval() -> int:
    try:
        return int(os.getenv("SCRAPER_INTERVAL_SECONDS", "3600"))
    except ValueError:
        return 3600


def load_job_configs() -> List[ScraperJobConfig]:
    raw = os.getenv("SCRAPER_JOBS", "[]")
    try:
        parsed = json.loads(raw) if raw else []
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse SCRAPER_JOBS configuration", error=str(exc))
        return []

    if not isinstance(parsed, list):
        logger.error("SCRAPER_JOBS must be a list of job definitions")
        return []

    configs: List[ScraperJobConfig] = []
    default_interval = _default_interval()

    for index, item in enumerate(parsed):
        if not isinstance(item, dict):
            logger.warning("Ignoring invalid job definition", job=item)
            continue

        name = str(item.get("name") or item.get("query") or f"job-{index}")
        interval = item.get("interval_seconds") or item.get("interval") or default_interval
        try:
            interval_seconds = int(interval)
            if interval_seconds <= 0:
                raise ValueError
        except (TypeError, ValueError):
            logger.warning("Invalid interval for job; using default", job=name, interval=interval)
            interval_seconds = default_interval

        params = {
            "query": item.get("query"),
            "location": item.get("location"),
            "radius": item.get("radius"),
            "min_price": item.get("min_price"),
            "max_price": item.get("max_price"),
            "page_count": int(item.get("page_count", 1) or 1),
        }
        is_active = bool(item.get("is_active", True))
        configs.append(
            ScraperJobConfig(
                name=name,
                interval_seconds=interval_seconds,
                params=params,
                is_active=is_active,
            )
        )

    return configs


class ScraperScheduler:
    """Runs scraping jobs at configured intervals."""

    def __init__(
        self,
        *,
        browser_manager,
        session_factory: async_sessionmaker,
        jobs: Optional[List[ScraperJobConfig]] = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._browser_manager = browser_manager
        self._session_factory = session_factory
        self._bootstrap_jobs = jobs or []
        self._jobs: Dict[int, SchedulerJobState] = {}
        self._tasks: Dict[int, asyncio.Task] = {}
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._event_bus = event_bus

    async def start(self) -> None:
        """Initialise scheduler jobs and launch active tasks."""

        async with self._session_factory() as session:
            repo = SchedulerJobRepository(session)

            # Ensure bootstrap jobs exist
            for config in self._bootstrap_jobs:
                existing = await repo.get_by_name(config.name)
                if existing is None:
                    logger.info(
                        "Bootstrapping scheduler job",
                        name=config.name,
                        interval=config.interval_seconds,
                    )
                    await repo.create_job(
                        name=config.name,
                        interval_seconds=config.interval_seconds,
                        params=config.params,
                        is_active=config.is_active,
                    )

            await session.commit()

            jobs = await repo.list_jobs()

        to_start: List[int] = []
        async with self._lock:
            self._jobs.clear()
            for job in jobs:
                state = self._build_state(job)
                self._jobs[state.id] = state
                if state.is_active:
                    to_start.append(state.id)

        for job_id in to_start:
            self._start_job_task(job_id)

        if not to_start:
            logger.info("Scraper scheduler initialised without active jobs")
        else:
            logger.info("Scraper scheduler started", active_jobs=len(to_start))

    async def shutdown(self) -> None:
        """Cancel all running tasks and reset scheduler state."""

        self._stop_event.set()
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        async with self._lock:
            self._tasks.clear()
            self._jobs.clear()
            self._stop_event = asyncio.Event()

    async def list_jobs(self) -> List[SchedulerJobState]:
        """Return a snapshot of current job states."""

        async with self._lock:
            return [self._copy_state(state) for state in self._jobs.values()]

    async def add_job(self, config: ScraperJobConfig) -> SchedulerJobState:
        """Persist and activate a new scheduler job."""

        async with self._session_factory() as session:
            repo = SchedulerJobRepository(session)
            existing = await repo.get_by_name(config.name)
            if existing is not None:
                raise ValueError(f"Job '{config.name}' existiert bereits")

            job = await repo.create_job(
                name=config.name,
                interval_seconds=config.interval_seconds,
                params=config.params,
                is_active=config.is_active,
            )
            await session.commit()

        state = self._build_state(job)
        async with self._lock:
            self._jobs[state.id] = state
            should_start = state.is_active

        if should_start:
            self._start_job_task(state.id)

        return self._copy_state(state)

    async def update_job(
        self,
        job_id: int,
        *,
        params: Optional[Dict[str, Any]] = None,
        interval_seconds: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> SchedulerJobState:
        """Update scheduler job configuration."""

        async with self._session_factory() as session:
            repo = SchedulerJobRepository(session)
            job = await repo.get_by_id(job_id)
            if job is None:
                raise ValueError("Job wurde nicht gefunden")

            current_params = job.params_dict()
            updated_params = current_params if params is None else {**current_params, **params}
            updated_interval = interval_seconds if interval_seconds is not None else job.interval_seconds
            updated_active = is_active if is_active is not None else job.is_active

            await repo.update_job(
                job,
                interval_seconds=updated_interval,
                params=updated_params,
                is_active=updated_active,
            )
            await session.commit()

        state = self._build_state(job)
        restart = False

        async with self._lock:
            self._jobs[state.id] = state
            if state.id in self._tasks:
                restart = state.is_active

        if restart:
            self._start_job_task(state.id)
        elif not state.is_active:
            self._cancel_job_task(state.id)

        return self._copy_state(state)

    async def set_job_active(self, job_id: int, active: bool) -> SchedulerJobState:
        """Enable or disable a scheduler job."""

        async with self._session_factory() as session:
            repo = SchedulerJobRepository(session)
            job = await repo.get_by_id(job_id)
            if job is None:
                raise ValueError("Job wurde nicht gefunden")

            await repo.update_job(job, is_active=active)
            await session.commit()

        state = self._build_state(job)

        async with self._lock:
            self._jobs[state.id] = state

        if active:
            self._start_job_task(state.id)
        else:
            self._cancel_job_task(state.id)

        return self._copy_state(state)

    async def delete_job(self, job_id: int) -> SchedulerJobState:
        """Remove a scheduler job from persistence and cancel it."""

        async with self._session_factory() as session:
            repo = SchedulerJobRepository(session)
            job = await repo.get_by_id(job_id)
            if job is None:
                raise ValueError("Job wurde nicht gefunden")

            await repo.delete_job(job)
            await session.commit()

        async with self._lock:
            state = self._jobs.pop(job_id, None)

        self._cancel_job_task(job_id)

        if state is None:
            raise ValueError("Jobzustand wurde nicht gefunden")

        return self._copy_state(state)

    async def run_job_once(self, job_id: int) -> SchedulerJobState:
        """Execute a scheduler job immediately."""

        async with self._lock:
            state = self._jobs.get(job_id)
            if state is None:
                raise ValueError("Job wurde nicht gefunden")
            running_task = self._tasks.get(job_id)

        if running_task and not running_task.done():
            raise RuntimeError("Job läuft bereits; bitte zunächst stoppen")

        await self._execute_job(state)
        async with self._lock:
            updated_state = self._jobs.get(job_id, state)

        return self._copy_state(updated_state)

    def _build_state(self, job) -> SchedulerJobState:
        return SchedulerJobState(
            id=job.id,
            name=job.name,
            interval_seconds=job.interval_seconds,
            params=job.params_dict(),
            is_active=job.is_active,
            created_at=job.created_at,
            updated_at=job.updated_at,
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
            last_run_status=job.last_run_status,
            last_run_message=job.last_run_message,
            last_run_duration_seconds=job.last_run_duration_seconds,
            last_result_count=job.last_result_count,
        )

    def _copy_state(self, state: SchedulerJobState) -> SchedulerJobState:
        return SchedulerJobState(
            id=state.id,
            name=state.name,
            interval_seconds=state.interval_seconds,
            params=dict(state.params),
            is_active=state.is_active,
            created_at=state.created_at,
            updated_at=state.updated_at,
            last_run_at=state.last_run_at,
            next_run_at=state.next_run_at,
            last_run_status=state.last_run_status,
            last_run_message=state.last_run_message,
            last_run_duration_seconds=state.last_run_duration_seconds,
            last_result_count=state.last_result_count,
        )

    def _start_job_task(self, job_id: int) -> None:

        async def runner() -> None:
            await self._run_job(job_id)

        self._cancel_job_task(job_id)
        task = asyncio.create_task(runner(), name=f"scraper-job-{job_id}")
        self._tasks[job_id] = task

    def _cancel_job_task(self, job_id: int) -> None:
        task = self._tasks.pop(job_id, None)
        if task and not task.done():
            task.cancel()

    async def _run_job(self, job_id: int) -> None:
        """Background task loop for a single job."""

        while not self._stop_event.is_set():
            async with self._lock:
                state = self._jobs.get(job_id)
            if state is None or not state.is_active:
                break

            logger.info("Scraper job started", job=state.name, interval=state.interval_seconds)
            try:
                await self._execute_job(state)
            except asyncio.CancelledError:
                logger.debug("Scraper job cancelled", job=state.name)
                raise
            except Exception:
                logger.exception("Scraper job crashed", job=state.name)

            # Wait for interval or until shutdown is requested
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=state.interval_seconds)
            except asyncio.TimeoutError:
                continue

        logger.debug("Scraper job loop stopped", job_id=job_id)

    async def _execute_job(self, state: SchedulerJobState) -> None:
        """Execute the scraping logic for a single job configuration."""

        logger.info("Executing scraper job", job=state.name, params=state.params)
        start_ts = time.perf_counter()
        now = datetime.now(timezone.utc)
        next_run = now + timedelta(seconds=state.interval_seconds)

        processed_count = 0
        skipped_count = 0
        last_error: Optional[str] = None
        status = "success"
        listings: List[Dict[str, Any]] = []
        analysis_events: List[ListingImagesUpdated] = []

        try:
            result = await fetch_listings(self._browser_manager, **state.params)
        except Exception:
            last_error = "Listing fetch failed"
            status = "error"
            logger.exception("Listing fetch failed", job=state.name)
        else:
            if not result or not isinstance(result, dict) or not result.get("success"):
                last_error = "Listing fetch returned no results"
                status = "error"
                logger.warning("Listing fetch returned no results", job=state.name)
            else:
                listings_data = result.get("results") or result.get("data") or []
                if isinstance(listings_data, list):
                    listings = listings_data
                else:
                    last_error = "Invalid listings result structure"
                    status = "error"
                    logger.error(
                        "Invalid listings type",
                        job=state.name,
                        listings_type=type(listings_data),
                    )

        async with self._session_factory() as session:
            scheduler_repo = SchedulerJobRepository(session)
            job_row = await scheduler_repo.get_by_id(state.id)
            if job_row is None:
                logger.error("Scheduler job missing in database", job_id=state.id)
                return

            if status == "success" and listings:
                repo = ListingRepository(session)
                for index, summary in enumerate(listings):
                    if not isinstance(summary, dict):
                        logger.warning(
                            "Invalid summary type",
                            job=state.name,
                            index=index,
                            type=type(summary),
                        )
                        skipped_count += 1
                        continue

                    external_id = summary.get("adid") or summary.get("id") or summary.get("external_id")
                    if not external_id or not isinstance(external_id, str):
                        logger.warning("Skipping listing without valid id", job=state.name, index=index)
                        skipped_count += 1
                        continue

                    try:
                        details = await fetch_listing_details(self._browser_manager, external_id)
                    except Exception:
                        logger.exception("Failed to fetch listing details", job=state.name, id=external_id)
                        skipped_count += 1
                        continue

                    try:
                        result = await repo.upsert_listing(summary, details, state.name, state.search_metadata)
                        await session.flush()
                        if (
                            self._event_bus is not None
                            and result.images_changed
                        ):
                            analysis_events.append(
                                ListingImagesUpdated(
                                    listing_id=result.listing.id,
                                    external_id=result.listing.external_id,
                                    image_urls=result.listing.image_urls or [],
                                )
                            )
                        processed_count += 1
                    except Exception:
                        logger.exception("Failed to persist listing", job=state.name, id=external_id)
                        skipped_count += 1

            duration = time.perf_counter() - start_ts
            await scheduler_repo.update_job(
                job=job_row,
                last_run_at=now,
                next_run_at=next_run,
                last_run_status=status,
                last_run_message=None
                if status == "success"
                else (last_error or "Unbekannter Fehler")[:512],
                last_run_duration_seconds=duration,
                last_result_count=processed_count,
            )
            await session.commit()

        if self._event_bus and analysis_events:
            for event in analysis_events:
                try:
                    await self._event_bus.publish(event)
                except Exception:
                    logger.exception(
                        "Failed to publish image analysis event",
                        listing_id=event.listing_id,
                        external_id=event.external_id,
                    )

        async with self._lock:
            existing = self._jobs.get(state.id)
            if existing:
                existing.last_run_at = now
                existing.next_run_at = next_run
                existing.last_run_status = status
                existing.last_run_message = (
                    None if status == "success" else (last_error or "Unbekannter Fehler")[:512]
                )
                existing.last_run_duration_seconds = duration
                existing.last_result_count = processed_count
                existing.updated_at = datetime.now(timezone.utc)

        logger.info(
            "Completed scheduler job",
            job=state.name,
            processed=processed_count,
            skipped=skipped_count,
            status=status,
        )
