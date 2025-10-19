"""Repository for Kleinanzeigen listing persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Listing


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
    ) -> Listing:
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
        listing.extra_info = (details or {}).get("extra_info")

        images: Iterable[str] | None = None
        if details and details.get("images"):
            images = [img for img in details["images"] if isinstance(img, str)]
        elif summary.get("image"):
            images = [summary["image"]]
        listing.image_urls = list(images) if images else []

        listing.update_timestamps()
        return listing

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
