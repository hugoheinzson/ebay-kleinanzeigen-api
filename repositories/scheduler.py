"""Repository for scheduler job management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ScheduledJob


class SchedulerJobRepository:
    """Encapsulates persistence logic for scheduled scraper jobs."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_jobs(self) -> List[ScheduledJob]:
        stmt = select(ScheduledJob).order_by(ScheduledJob.created_at.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, job_id: int) -> Optional[ScheduledJob]:
        stmt = select(ScheduledJob).where(ScheduledJob.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[ScheduledJob]:
        stmt = select(ScheduledJob).where(ScheduledJob.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_job(
        self,
        *,
        name: str,
        interval_seconds: int,
        params: Dict[str, Any],
        is_active: bool = True,
    ) -> ScheduledJob:
        job = ScheduledJob(
            name=name,
            interval_seconds=interval_seconds,
            is_active=is_active,
            query=params.get("query"),
            location=params.get("location"),
            radius=params.get("radius"),
            min_price=params.get("min_price"),
            max_price=params.get("max_price"),
            page_count=int(params.get("page_count") or 1),
        )
        job.update_timestamp()
        self.session.add(job)
        await self.session.flush()
        logger.debug("Created scheduler job", job_id=job.id, name=job.name)
        return job

    async def update_job(
        self,
        job: ScheduledJob,
        *,
        interval_seconds: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None,
        last_run_at: Optional[datetime] = None,
        next_run_at: Optional[datetime] = None,
        last_run_status: Optional[str] = None,
        last_run_message: Optional[str] = None,
        last_run_duration_seconds: Optional[float] = None,
        last_result_count: Optional[int] = None,
    ) -> ScheduledJob:
        if interval_seconds is not None:
            job.interval_seconds = interval_seconds
        if params is not None:
            job.query = params.get("query")
            job.location = params.get("location")
            job.radius = params.get("radius")
            job.min_price = params.get("min_price")
            job.max_price = params.get("max_price")
            job.page_count = int(params.get("page_count") or 1)
        if is_active is not None:
            job.is_active = is_active
        if last_run_at is not None:
            job.last_run_at = last_run_at
        if next_run_at is not None:
            job.next_run_at = next_run_at
        if last_run_status is not None:
            job.last_run_status = last_run_status
        if last_run_message is not None:
            job.last_run_message = last_run_message
        if last_run_duration_seconds is not None:
            job.last_run_duration_seconds = last_run_duration_seconds
        if last_result_count is not None:
            job.last_result_count = last_result_count

        job.update_timestamp()
        await self.session.flush()
        logger.debug("Updated scheduler job", job_id=job.id, name=job.name)
        return job

    async def delete_job(self, job: ScheduledJob) -> None:
        await self.session.delete(job)
        await self.session.flush()
        logger.debug("Deleted scheduler job", job_id=job.id, name=job.name)
