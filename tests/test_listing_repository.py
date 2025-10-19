import os
from datetime import datetime, timezone

import pytest

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

pytest.importorskip("sqlalchemy")

from db import init_db, get_session_factory, reset_database_state  # noqa: E402
from repositories import ListingRepository  # noqa: E402


@pytest.fixture()
async def session():
    await reset_database_state()
    await init_db()
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.mark.asyncio
async def test_upsert_and_retrieve_listing(session):
    repo = ListingRepository(session)

    summary = {
        "adid": "123",
        "title": "Woom 3 Fahrrad",
        "description": "Leichtes Kinderfahrrad",
        "price": "450",
        "url": "https://example.com/listing",
        "image": "https://example.com/image.jpg",
    }
    details = {
        "id": "123",
        "title": "Woom 3 Kinderfahrrad",
        "description": "Sehr gut erhaltenes Rad",
        "status": "active",
        "delivery": "pickup",
        "categories": ["Fahrräder"],
        "location": {"zip": "10115", "city": "Berlin", "state": "Berlin"},
        "seller": {"name": "Anna", "badges": ["Top"]},
        "price": {"amount": "450", "currency": "EUR", "negotiable": True},
        "images": ["https://example.com/image.jpg", "https://example.com/image2.jpg"],
        "extra_info": {"created_at": "15.01.2024, 13:45"},
    }

    result = await repo.upsert_listing(summary, details, "woom-3", {"query": "Woom 3"})
    assert result.was_created is True
    assert result.images_changed is True
    await session.commit()

    listings, total = await repo.list_listings(limit=10, offset=0)
    assert total == 1
    assert listings[0].title == "Woom 3 Kinderfahrrad"
    assert listings[0].image_urls == [
        "https://example.com/image.jpg",
        "https://example.com/image2.jpg",
    ]
    assert listings[0].is_suspicious is False
    assert listings[0].suspicion_reason is None
    assert listings[0].posted_at == datetime(2024, 1, 15, 12, 45, tzinfo=timezone.utc)
    assert listings[0].posted_at_text == "15.01.2024, 13:45"

    filtered, filtered_total = await repo.list_listings(
        limit=10, offset=0, query_name="woom-3", search_term="Kinderfahrrad"
    )
    assert filtered_total == 1
    assert filtered[0].status == "active"

    listing = await repo.get_by_external_id("123")
    assert listing is not None
    assert listing.price_amount == "450"
    assert listing.price_negotiable is True
