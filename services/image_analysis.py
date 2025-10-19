"""Image analysis background service for detecting suspicious listings."""

from __future__ import annotations

import asyncio
import io
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Awaitable, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import httpx
import imagehash
import numpy as np
from loguru import logger
from PIL import Image, UnidentifiedImageError
from prometheus_client import Counter, Histogram
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from db.models import ImageFingerprint, Listing
from events import ListingAnalysisCompleted, ListingImagesUpdated
from repositories import ImageFingerprintRepository, ListingRepository
from services.event_bus import EventBus


IMAGE_ANALYSIS_DURATION = Histogram(
    "image_analysis_duration_seconds",
    "Processing latency for listing image analysis",
    labelnames=["status"],
)
IMAGE_ANALYSIS_COUNTER = Counter(
    "image_analysis_events_total",
    "Count of processed listing image analysis events",
    labelnames=["status"],
)


@dataclass(slots=True)
class AnalysisConfig:
    """Runtime configuration for image analysis."""

    hash_method: str = "phash"
    phash_threshold: int = 5
    fetch_timeout_seconds: float = 15.0
    max_image_bytes: int = 10_000_000  # 10 MB safeguard
    parallel_downloads: int = 3


class ImageAnalysisService:
    """Background worker that consumes listing image events and marks suspicious listings."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker,
        event_bus: EventBus,
        config: Optional[AnalysisConfig] = None,
        image_fetcher: Optional[Callable[[str], Awaitable[Optional[bytes]]]] = None,
    ) -> None:
        self._session_factory = session_factory
        self._event_bus = event_bus
        self._config = config or AnalysisConfig()
        self._queue: asyncio.Queue[ListingImagesUpdated] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._http_client: httpx.AsyncClient | None = None
        self._started = False
        self._image_fetcher = image_fetcher

        self._event_bus.subscribe(ListingImagesUpdated, self._enqueue_event)

    async def start(self) -> None:
        if self._started:
            return

        self._started = True
        self._http_client = httpx.AsyncClient(timeout=self._config.fetch_timeout_seconds)
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("ImageAnalysisService started")

    async def stop(self) -> None:
        if not self._started:
            return

        self._started = False
        await self._queue.put(None)  # type: ignore[arg-type]
        if self._worker_task:
            await self._worker_task
            self._worker_task = None
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
        logger.info("ImageAnalysisService stopped")

    async def _enqueue_event(self, event: ListingImagesUpdated) -> None:
        await self._queue.put(event)

    async def _process_events(self) -> None:
        while True:
            event = await self._queue.get()
            if event is None:
                self._queue.task_done()
                break

            status_label = "success"
            started = time.perf_counter()
            try:
                await self._handle_event(event)
            except Exception:
                IMAGE_ANALYSIS_COUNTER.labels(status="error").inc()
                logger.exception(
                    "Image analysis failed",
                    listing_id=event.listing_id,
                    external_id=event.external_id,
                )
                status_label = "error"
            else:
                IMAGE_ANALYSIS_COUNTER.labels(status="success").inc()
            finally:
                duration = time.perf_counter() - started
                IMAGE_ANALYSIS_DURATION.labels(status=status_label).observe(duration)
                self._queue.task_done()

    async def _handle_event(self, event: ListingImagesUpdated) -> None:
        if not event.image_urls:
            logger.debug(
                "Skipping analysis for listing without images",
                listing_id=event.listing_id,
            )
            return

        async with self._session_factory() as session:
            repo = ListingRepository(session)

            listing = await session.get(Listing, event.listing_id)
            if listing is None:
                logger.warning(
                    "Received analysis event for missing listing",
                    listing_id=event.listing_id,
                )
                return

            if not event.image_urls:
                await repo.clear_suspicion(listing)
                await session.commit()
                await self._event_bus.publish(
                    ListingAnalysisCompleted(
                        listing_id=listing.id,
                        external_id=listing.external_id,
                        is_suspicious=False,
                        reason=None,
                        confidence=None,
                        meta=None,
                    )
                )
                logger.debug(
                    "Cleared suspicion for listing without images",
                    listing_id=event.listing_id,
                )
                return

            fingerprint_repo = ImageFingerprintRepository(session)
            await fingerprint_repo.delete_for_listing(listing.id)

            existing_fingerprints = await fingerprint_repo.list_all(
                exclude_listing=listing.id
            )

            match_candidates: List[Tuple[ImageFingerprint, int]] = []

            async for fingerprint in self._compute_fingerprints(listing.id, event.image_urls):
                self._update_similarity_matches(
                    fingerprint, existing_fingerprints, match_candidates
                )
                session.add(fingerprint)

            await session.flush()

            matched_listing_ids = {fingerprint.listing_id for fingerprint, _ in match_candidates}
            matched_listings: Dict[int, Listing] = {}
            if matched_listing_ids:
                stmt = select(Listing).where(Listing.id.in_(matched_listing_ids))
                result = await session.execute(stmt)
                matched_list = result.scalars().all()
                matched_listings = {item.id: item for item in matched_list}

            matches_payload = [
                {
                    "listing_id": fp.listing_id,
                    "external_id": matched_listings.get(fp.listing_id).external_id
                    if matched_listings.get(fp.listing_id)
                    else None,
                    "image_url": fp.image_url,
                    "hash_hex": fp.hash_hex,
                    "hamming_distance": diff,
                }
                for fp, diff in match_candidates
            ]

            if matched_listing_ids:
                meta = {
                    "hash_method": self._config.hash_method,
                    "threshold": self._config.phash_threshold,
                    "matches": matches_payload,
                }
                confidence = self._estimate_confidence([diff for _, diff in match_candidates])
                await repo.mark_suspicion(
                    listing,
                    reason="duplicate-image",
                    confidence=confidence,
                    meta=meta,
                )
                await self._propagate_matches(
                    repo,
                    source_listing=listing,
                    match_fingerprints=match_candidates,
                    matched_listings=matched_listings,
                )
                outcome = ListingAnalysisCompleted(
                    listing_id=listing.id,
                    external_id=listing.external_id,
                    is_suspicious=True,
                    reason="duplicate-image",
                    confidence=confidence,
                    meta=meta,
                )
            else:
                await repo.clear_suspicion(listing)
                outcome = ListingAnalysisCompleted(
                    listing_id=listing.id,
                    external_id=listing.external_id,
                    is_suspicious=False,
                    reason=None,
                    confidence=None,
                    meta=None,
                )

            await session.commit()
            await self._event_bus.publish(outcome)

    async def _compute_fingerprints(
        self,
        listing_id: int,
        image_urls: Sequence[str],
    ) -> AsyncIterator[ImageFingerprint]:
        semaphore = asyncio.Semaphore(self._config.parallel_downloads)

        async def process(url: str) -> Optional[ImageFingerprint]:
            async with semaphore:
                image_bytes = await self._fetch_image(url)
                if image_bytes is None:
                    return None

                return self._build_fingerprint(listing_id, url, image_bytes)

        tasks = [asyncio.create_task(process(url)) for url in image_urls]
        for task in asyncio.as_completed(tasks):
            fingerprint = await task
            if fingerprint is not None:
                yield fingerprint

    async def _fetch_image(self, url: str) -> Optional[bytes]:
        if self._image_fetcher is not None:
            return await self._image_fetcher(url)

        if self._http_client is None:
            raise RuntimeError("ImageAnalysisService not started")

        try:
            response = await self._http_client.get(url)
            response.raise_for_status()
            content = response.content
            if len(content) > self._config.max_image_bytes:
                logger.warning("Image exceeds max size limit", url=url)
                return None
            return content
        except httpx.HTTPError:
            logger.warning("Failed to download image", url=url)
            return None

    def _build_fingerprint(self, listing_id: int, url: str, data: bytes) -> Optional[ImageFingerprint]:
        buffer = io.BytesIO(data)
        try:
            with Image.open(buffer) as img:
                img = img.convert("RGB")
                hash_value = imagehash.phash(img)
                width, height = img.size
        except (UnidentifiedImageError, OSError):
            logger.warning("Unsupported image format", url=url)
            return None

        hash_hex = hash_value.__str__()
        hash_bits = self._hash_to_int(hash_value)

        fingerprint = ImageFingerprint(
            listing_id=listing_id,
            image_url=url,
            hash_method=self._config.hash_method,
            hash_hex=hash_hex,
            hash_bits=hash_bits,
            width=width,
            height=height,
            file_size=len(data),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        return fingerprint

    def _hash_to_int(self, hash_value: imagehash.ImageHash) -> int:
        array = np.array(hash_value.hash, dtype=np.uint8).reshape(-1)
        result = 0
        for bit in array:
            result = (result << 1) | int(bit)
        return result

    def _update_similarity_matches(
        self,
        fingerprint: ImageFingerprint,
        candidates: Iterable[ImageFingerprint],
        matches: List[Tuple[ImageFingerprint, int]],
    ) -> None:
        for candidate in candidates:
            if candidate.hash_method != fingerprint.hash_method:
                continue

            candidate_bits = (
                candidate.hash_bits
                if candidate.hash_bits is not None
                else int(candidate.hash_hex, 16)
            )
            diff = self._hamming_distance(
                fingerprint.hash_bits or int(fingerprint.hash_hex, 16),
                candidate_bits,
            )
            if diff <= self._config.phash_threshold:
                matches.append((candidate, diff))

    def _hamming_distance(self, a: int, b: int) -> int:
        return int(bin(a ^ b).count("1"))

    def _estimate_confidence(self, diffs: Sequence[int]) -> float:
        if not diffs:
            return 0.0
        bit_length = 64  # phash outputs 64-bit hashes
        best = min(diffs)
        return round(1 - (best / bit_length), 3)

    async def _propagate_matches(
        self,
        repo: ListingRepository,
        *,
        source_listing: Listing,
        match_fingerprints: Sequence[Tuple[ImageFingerprint, int]],
        matched_listings: Dict[int, Listing],
    ) -> None:
        if not matched_listings:
            return

        for fingerprint, diff in match_fingerprints:
            listing = matched_listings.get(fingerprint.listing_id)
            if listing is None:
                continue

            meta = listing.suspicion_meta or {"matches": []}
            matches = meta.setdefault("matches", [])
            matches.append(
                {
                    "listing_id": source_listing.id,
                    "external_id": source_listing.external_id,
                    "image_url": fingerprint.image_url,
                    "hash_hex": fingerprint.hash_hex,
                    "hamming_distance": diff,
                    "threshold": self._config.phash_threshold,
                }
            )
            meta["hash_method"] = self._config.hash_method

            await repo.mark_suspicion(
                listing,
                reason="duplicate-image",
                confidence=None,
                meta=meta,
            )
