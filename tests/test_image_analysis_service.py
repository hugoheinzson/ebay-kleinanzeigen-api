import io
import os
from typing import List

import pytest
from PIL import Image

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

pytest.importorskip("sqlalchemy")

from db import init_db, get_session_factory, reset_database_state  # noqa: E402
from events import ListingImagesUpdated  # noqa: E402
from repositories import ListingRepository  # noqa: E402
from services.image_analysis import ImageAnalysisService  # noqa: E402


def create_image_bytes(color: str) -> bytes:
    image = Image.new("RGB", (64, 64), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class StubEventBus:
    def __init__(self) -> None:
        self.subscriptions: List = []
        self.published = []

    def subscribe(self, event_type, handler):
        self.subscriptions.append((event_type, handler))

    async def publish(self, event):
        self.published.append(event)


@pytest.fixture()
async def session_factory():
    await reset_database_state()
    await init_db()
    return get_session_factory()


@pytest.mark.asyncio
async def test_duplicate_images_mark_listings_suspicious(session_factory):
    bus = StubEventBus()

    image_store = {
        "https://example.com/a.png": create_image_bytes("red"),
        "https://example.com/b.png": create_image_bytes("red"),
    }

    async def fetcher(url: str):
        return image_store[url]

    service = ImageAnalysisService(
        session_factory=session_factory,
        event_bus=bus,
        image_fetcher=fetcher,
    )

    async with session_factory() as session:
        repo = ListingRepository(session)
        result1 = await repo.upsert_listing(
            {"adid": "a", "title": "A", "image": "https://example.com/a.png"},
            {"id": "a", "images": ["https://example.com/a.png"]},
            "job",
            {},
        )
        result2 = await repo.upsert_listing(
            {"adid": "b", "title": "B", "image": "https://example.com/b.png"},
            {"id": "b", "images": ["https://example.com/b.png"]},
            "job",
            {},
        )
        await session.commit()

    await service._handle_event(
        ListingImagesUpdated(
            listing_id=result1.listing.id,
            external_id=result1.listing.external_id,
            image_urls=result1.listing.image_urls,
        )
    )

    async with session_factory() as session:
        repo = ListingRepository(session)
        listing1 = await repo.get_by_external_id("a")
        assert listing1 is not None
        assert listing1.is_suspicious is False

    await service._handle_event(
        ListingImagesUpdated(
            listing_id=result2.listing.id,
            external_id=result2.listing.external_id,
            image_urls=result2.listing.image_urls,
        )
    )

    async with session_factory() as session:
        repo = ListingRepository(session)
        listing1 = await repo.get_by_external_id("a")
        listing2 = await repo.get_by_external_id("b")

        assert listing1 is not None
        assert listing2 is not None
        assert listing1.is_suspicious is True
        assert listing2.is_suspicious is True
        assert listing2.suspicion_reason == "duplicate-image"
        assert listing2.suspicion_meta is not None
        assert listing2.suspicion_meta["matches"]
