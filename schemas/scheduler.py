"""Pydantic schemas for scheduler job management."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SchedulerJobBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    query: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    radius: Optional[int] = Field(None, ge=0)
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    page_count: int = Field(1, ge=1, le=20)
    interval_seconds: int = Field(3600, ge=60, description="Interval in seconds between runs")
    is_active: bool = Field(True, description="Whether the scheduler should run this job")


class SchedulerJobCreate(SchedulerJobBase):
    """Payload for creating scheduler jobs."""


class SchedulerJobUpdate(BaseModel):
    query: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    radius: Optional[int] = Field(None, ge=0)
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    page_count: Optional[int] = Field(None, ge=1, le=20)
    interval_seconds: Optional[int] = Field(None, ge=60)
    is_active: Optional[bool] = None


class SchedulerJobResponse(SchedulerJobBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    last_run_message: Optional[str] = None
    last_run_duration_seconds: Optional[float] = None
    last_result_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SchedulerJobsResponse(BaseModel):
    jobs: List[SchedulerJobResponse]


class SchedulerJobActionResponse(BaseModel):
    job: SchedulerJobResponse
    message: str
