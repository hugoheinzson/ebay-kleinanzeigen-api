"""Background scheduler for periodic scraping jobs."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import async_sessionmaker

from repositories import ListingRepository
from services.kleinanzeigen import fetch_listings, fetch_listing_details


@dataclass(slots=True)
class ScraperJobConfig:
    """Configuration for a scraping job."""

    name: str
    interval_seconds: int
    params: Dict[str, Any]

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
        configs.append(ScraperJobConfig(name=name, interval_seconds=interval_seconds, params=params))

    return configs


class ScraperScheduler:
    """Runs scraping jobs at configured intervals."""

    def __init__(
        self,
        *,
        browser_manager,
        session_factory: async_sessionmaker,
        jobs: Optional[List[ScraperJobConfig]] = None,
    ) -> None:
        self._browser_manager = browser_manager
        self._session_factory = session_factory
        self._jobs = jobs or []
        self._tasks: List[asyncio.Task] = []
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if not self._jobs:
            logger.info("No scraper jobs configured; scheduler idle")
            return
        logger.info("Starting scraper scheduler", job_count=len(self._jobs))
        for job in self._jobs:
            task = asyncio.create_task(self._run_job(job), name=f"scraper-{job.name}")
            self._tasks.append(task)

    async def shutdown(self) -> None:
        self._stop_event.set()
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._stop_event = asyncio.Event()

    async def _run_job(self, job: ScraperJobConfig) -> None:
        logger.info("Scraper job started", job=job.name, interval=job.interval_seconds)
        try:
            while not self._stop_event.is_set():
                await self._execute_job(job)
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=job.interval_seconds)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            logger.debug("Scraper job cancelled", job=job.name)
        except Exception:
            logger.exception("Scraper job crashed", job=job.name)

    async def _execute_job(self, job: ScraperJobConfig) -> None:
        logger.info("Executing scraper job", job=job.name, params=job.params)
        try:
            result = await fetch_listings(self._browser_manager, **job.params)
        except Exception:
            logger.exception("Listing fetch failed", job=job.name)
            return

        if not result or not result.get("success"):
            logger.warning("Listing fetch returned no results", job=job.name, response=result)
            return

        listings = result.get("results") or result.get("data") or []
        if not listings:
            logger.info("No listings found for job", job=job.name)
            return

        async with self._session_factory() as session:
            repo = ListingRepository(session)
            for summary in listings:
                external_id = summary.get("adid") or summary.get("id")
                if not external_id:
                    logger.debug("Skipping listing without id", job=job.name)
                    continue

                details = None
                try:
                    details = await fetch_listing_details(self._browser_manager, external_id)
                except Exception:
                    logger.exception("Failed to fetch listing details", id=external_id)

                try:
                    await repo.upsert_listing(summary, details, job.name, job.search_metadata)
                except Exception:
                    logger.exception("Failed to persist listing", id=external_id)
            await session.commit()
