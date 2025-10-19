"""Pydantic schemas for stored listings."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SellerSchema(BaseModel):
    name: Optional[str] = None
    since: Optional[str] = None
    type: Optional[str] = None
    badges: List[str] = Field(default_factory=list)


class LocationSchema(BaseModel):
    zip: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class ListingResponse(BaseModel):
    external_id: str
    query_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price_amount: Optional[str] = None
    price_currency: Optional[str] = None
    price_negotiable: Optional[bool] = None
    price_text: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    delivery: Optional[str] = None
    thumbnail_url: Optional[str] = None
    categories: Optional[List[str]] = None
    location: Optional[LocationSchema] = None
    seller: Optional[SellerSchema] = None
    details: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    extra_info: Optional[Dict[str, Any]] = None
    image_urls: List[str] = Field(default_factory=list)
    search_params: Optional[Dict[str, Any]] = None
    first_seen_at: datetime
    last_seen_at: datetime
    posted_at: Optional[datetime] = None
    posted_at_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    is_suspicious: bool = False
    suspicion_reason: Optional[str] = None
    suspicion_confidence: Optional[float] = None
    suspicion_meta: Optional[Dict[str, Any]] = None
    last_analyzed_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class ListingPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ListingResponse]
