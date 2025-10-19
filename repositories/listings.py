"""Repository for Kleinanzeigen listing persistence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing

_TIME_PATTERN = re.compile(r"(\d{1,2})[:.](\d{2})")
_DATE_PATTERN = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})")
_BERLIN_TZ = ZoneInfo("Europe/Berlin")


@dataclass(slots=True)
class ListingUpsertResult:
    """Result metadata for listing persistence."""

    listing: Listing
    was_created: bool
    images_changed: bool


def _normalize_amount(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return str(Decimal(value))
        except InvalidOperation:
            return None
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace(".", "").replace(",", ".")
    try:
        return str(Decimal(normalized))
    except InvalidOperation:
        logger.debug("Failed to normalise price amount", value=value)
        return None


def _parse_posted_at(raw: Any) -> Tuple[Optional[datetime], Optional[str]]:
    if not isinstance(raw, str):
        return None, None

    text = raw.strip()
    if not text:
        return None, None

    normalized = text.replace("Uhr", "").replace("Uhr.", "").strip()
    normalized_lower = normalized.lower()

    now_berlin = datetime.now(_BERLIN_TZ)
    base: Optional[datetime] = None

    time_match = _TIME_PATTERN.search(normalized)
    hour: Optional[int] = int(time_match.group(1)) if time_match else None
    minute: Optional[int] = int(time_match.group(2)) if time_match else None

    date_match = _DATE_PATTERN.search(normalized)
    if normalized_lower.startswith("heute"):
        base = now_berlin
    elif normalized_lower.startswith("gestern"):
        base = now_berlin - timedelta(days=1)
    elif date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))
        if year < 100:
            year += 2000
        base = datetime(year, month, day, tzinfo=_BERLIN_TZ)

    posted_at: Optional[datetime] = None
    if base is not None:
        hour_value = hour if hour is not None else base.hour
        minute_value = minute if minute is not None else base.minute
        posted_at = base.replace(hour=hour_value, minute=minute_value, second=0, microsecond=0)
    elif date_match and hour is not None and minute is not None:
        # Fallback if there was a date but no base identified (shouldn't happen)
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))
        if year < 100:
            year += 2000
        posted_at = datetime(year, month, day, hour, minute, tzinfo=_BERLIN_TZ)

    if posted_at is not None:
        return posted_at.astimezone(timezone.utc), text

    # Strings such as "Vor 2 Stunden" cannot be deterministically converted; keep raw text
    return None, text


class ListingRepository:
    """Encapsulates persistence logic for listings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_listing(
        self,
        summary: Dict[str, Any],
        details: Optional[Dict[str, Any]],
        query_name: Optional[str],
        search_params: Optional[Dict[str, Any]],
    ) -> ListingUpsertResult:
        now = datetime.now(timezone.utc)
        external_id = (
            (details or {}).get("id")
            or summary.get("adid")
            or summary.get("id")
        )
        if not external_id:
            raise ValueError("Missing external id for listing persistence")

        stmt = select(Listing).where(Listing.external_id == external_id)
        result = await self.session.execute(stmt)
        listing = result.scalar_one_or_none()

        was_created = listing is None
        if listing is None:
            listing = Listing(
                external_id=external_id,
                first_seen_at=now,
                last_seen_at=now,
            )
            self.session.add(listing)
        else:
            listing.last_seen_at = now

        listing.query_name = query_name or summary.get("query")
        listing.search_params = search_params
        listing.title = (details or {}).get("title") or summary.get("title")
        listing.description = (details or {}).get("description") or summary.get("description")

        price_info = (details or {}).get("price")
        listing.price_amount = _normalize_amount(price_info.get("amount")) if price_info else None
        listing.price_currency = price_info.get("currency") if price_info else None
        listing.price_negotiable = price_info.get("negotiable") if price_info else None
        listing.price_text = summary.get("price") or (price_info.get("amount") if price_info else None)

        listing.url = summary.get("url") or (details or {}).get("url")
        listing.status = (details or {}).get("status")
        listing.delivery = (details or {}).get("delivery")
        listing.thumbnail_url = summary.get("image")
        listing.categories = (details or {}).get("categories")
        listing.location = (details or {}).get("location")
        listing.seller = (details or {}).get("seller")
        listing.details = (details or {}).get("details")
        listing.features = (details or {}).get("features")
        extra_info = (details or {}).get("extra_info") if details else None
        listing.extra_info = extra_info

        previous_images = set(listing.image_urls or [])
        images: Iterable[str] | None = None
        if details and details.get("images"):
            images = [img for img in details["images"] if isinstance(img, str)]
        elif summary.get("image"):
            images = [summary["image"]]
        listing.image_urls = list(images) if images else []
        images_changed = previous_images != set(listing.image_urls or [])

        posted_source: Optional[Any] = None
        if isinstance(extra_info, dict):
            posted_source = extra_info.get("created_at")
        if posted_source is None and details:
            posted_source = details.get("created_at")
        if posted_source:
            posted_at_dt, posted_text = _parse_posted_at(posted_source)
            if posted_at_dt is not None:
                listing.posted_at = posted_at_dt
            if posted_text and (posted_at_dt is not None or listing.posted_at_text is None):
                listing.posted_at_text = posted_text

        listing.update_timestamps()
        return ListingUpsertResult(
            listing=listing,
            was_created=was_created,
            images_changed=images_changed or was_created,
        )

    async def list_listings(
        self,
        *,
        limit: int,
        offset: int,
        query_name: Optional[str] = None,
        status: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> Tuple[List[Listing], int]:
        filters = []
        if query_name:
            filters.append(Listing.query_name == query_name)
        if status:
            filters.append(Listing.status == status)
        if search_term:
            pattern = f"%{search_term.lower()}%"
            title_match = func.lower(func.coalesce(Listing.title, "")).like(pattern)
            description_match = func.lower(func.coalesce(Listing.description, "")).like(pattern)
            filters.append(title_match | description_match)

        stmt = select(Listing)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(Listing.last_seen_at.desc())

        count_stmt = select(func.count(Listing.id))
        if filters:
            count_stmt = count_stmt.where(*filters)

        total = (await self.session.execute(count_stmt)).scalar_one()
        result = await self.session.execute(stmt.offset(offset).limit(limit))
        listings = result.scalars().all()
        return listings, total

    async def get_by_external_id(self, external_id: str) -> Optional[Listing]:
        stmt = select(Listing).where(Listing.external_id == external_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_suspicion(
        self,
        listing: Listing,
        *,
        reason: str,
        confidence: Optional[float],
        meta: Optional[Dict[str, Any]],
    ) -> Listing:
        listing.is_suspicious = True
        listing.suspicion_reason = reason
        listing.suspicion_confidence = confidence
        listing.suspicion_meta = meta
        listing.last_analyzed_at = datetime.now(timezone.utc)
        listing.update_timestamps()
        return listing

    async def clear_suspicion(self, listing: Listing) -> Listing:
        listing.is_suspicious = False
        listing.suspicion_reason = None
        listing.suspicion_confidence = None
        listing.suspicion_meta = None
        listing.last_analyzed_at = datetime.now(timezone.utc)
        listing.update_timestamps()
        return listing
