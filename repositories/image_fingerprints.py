"""Repository helpers for image fingerprint persistence and lookup."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ImageFingerprint


class ImageFingerprintRepository:
    """Encapsulates CRUD operations for image fingerprints."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def delete_for_listing(self, listing_id: int) -> None:
        stmt = delete(ImageFingerprint).where(ImageFingerprint.listing_id == listing_id)
        await self.session.execute(stmt)

    async def add_fingerprint(
        self,
        *,
        listing_id: int,
        image_url: str,
        hash_method: str,
        hash_hex: str,
        hash_bits: Optional[int],
        width: Optional[int],
        height: Optional[int],
        file_size: Optional[int],
    ) -> ImageFingerprint:
        now = datetime.now(timezone.utc)
        fingerprint = ImageFingerprint(
            listing_id=listing_id,
            image_url=image_url,
            hash_method=hash_method,
            hash_hex=hash_hex,
            hash_bits=hash_bits,
            width=width,
            height=height,
            file_size=file_size,
            created_at=now,
            updated_at=now,
        )
        self.session.add(fingerprint)
        return fingerprint

    async def list_all(self, *, exclude_listing: Optional[int] = None) -> List[ImageFingerprint]:
        stmt = select(ImageFingerprint)
        if exclude_listing is not None:
            stmt = stmt.where(ImageFingerprint.listing_id != exclude_listing)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_listing(self, listing_id: int) -> List[ImageFingerprint]:
        stmt = select(ImageFingerprint).where(ImageFingerprint.listing_id == listing_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
