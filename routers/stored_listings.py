"""API endpoints for persisted Kleinanzeigen listings."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_session
from repositories import ListingRepository
from schemas import ListingPage, ListingResponse


def _serialize_listing(listing) -> ListingResponse:
    data = ListingResponse.model_validate(listing)
    if data.image_urls is None:
        data.image_urls = []
    return data

router = APIRouter(prefix="/stored-listings", tags=["stored-listings"])


@router.get("", response_model=ListingPage)
async def list_stored_listings(
    *,
    session: AsyncSession = Depends(get_session),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    query_name: str | None = Query(None, description="Filter by configured job name"),
    status: str | None = Query(None, description="Filter by listing status"),
    search: str | None = Query(None, description="Search in title and description"),
) -> ListingPage:
    repo = ListingRepository(session)
    listings, total = await repo.list_listings(
        limit=limit,
        offset=offset,
        query_name=query_name,
        status=status,
        search_term=search,
    )

    items = [_serialize_listing(listing) for listing in listings]
    return ListingPage(total=total, limit=limit, offset=offset, items=items)


@router.get("/{external_id}", response_model=ListingResponse)
async def get_stored_listing(
    external_id: str,
    session: AsyncSession = Depends(get_session),
) -> ListingResponse:
    repo = ListingRepository(session)
    listing = await repo.get_by_external_id(external_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _serialize_listing(listing)
