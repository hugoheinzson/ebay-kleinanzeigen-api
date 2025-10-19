"""Listing domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass(slots=True)
class ListingImagesUpdated:
    """Triggered when a listing has new or updated images that require analysis."""

    listing_id: int
    external_id: str
    image_urls: List[str]
    triggered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(slots=True)
class ListingAnalysisCompleted:
    """Emitted after image analysis finished."""

    listing_id: int
    external_id: str
    is_suspicious: bool
    reason: Optional[str]
    confidence: Optional[float]
    meta: Optional[Dict[str, object]]
    analyzed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
