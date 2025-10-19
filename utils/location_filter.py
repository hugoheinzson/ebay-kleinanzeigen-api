"""Geolocation utilities for filtering listings by distance."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pgeocode  # type: ignore[import]

PostalCoordinates = Tuple[float, float]

_POSTAL_CODE_PATTERN = re.compile(r"\b\d{5}\b")


@lru_cache(maxsize=1)
def _nominatim() -> pgeocode.Nominatim:
    """Return cached nominatim instance for German postal codes."""
    return pgeocode.Nominatim("de")


def _is_valid_coordinate(value: Optional[float]) -> bool:
    if value is None:
        return False
    try:
        return not math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def _coords_from_series(series: Any) -> Optional[PostalCoordinates]:
    """Extract coordinates from pgeocode results."""
    if series is None:
        return None

    latitude = getattr(series, "latitude", None)
    longitude = getattr(series, "longitude", None)

    if not (_is_valid_coordinate(latitude) and _is_valid_coordinate(longitude)):
        return None

    return float(latitude), float(longitude)


def _extract_postal_code(text: str) -> Optional[str]:
    """Extract the first 5-digit German postal code from a string."""
    match = _POSTAL_CODE_PATTERN.search(text)
    return match.group(0) if match else None


def resolve_location_coordinates(location: str) -> Optional[PostalCoordinates]:
    """
    Resolve a human-readable location string to latitude/longitude coordinates.

    The resolver first looks for an explicit postal code inside the text. If none is
    found it relies on the pgeocode location lookup which performs fuzzy matching on
    German city names.
    """
    if not location:
        return None

    location = location.strip()
    if not location:
        return None

    # Prefer explicit postal codes embedded in the string
    postal_code = _extract_postal_code(location)
    if postal_code:
        coords = resolve_postal_code_coordinates(postal_code)
        if coords:
            return coords

    # Fallback to fuzzy search by city name
    results = _nominatim().query_location(location)
    if results is None or getattr(results, "empty", False):
        return None

    # query_location may return either a pandas Series or DataFrame depending on matches
    if hasattr(results, "latitude"):
        return _coords_from_series(results)

    # If a DataFrame is returned, iterate over rows until a valid coordinate is found
    for _, row in results.iterrows():  # type: ignore[attr-defined]
        coords = _coords_from_series(row)
        if coords:
            return coords

    return None


@lru_cache(maxsize=4096)
def resolve_postal_code_coordinates(postal_code: str) -> Optional[PostalCoordinates]:
    """Resolve a German postal code to coordinates using pgeocode."""
    if not postal_code:
        return None

    cleaned = postal_code.strip()
    if not cleaned:
        return None

    result = _nominatim().query_postal_code(cleaned)
    return _coords_from_series(result)


def _haversine_km(origin: PostalCoordinates, destination: PostalCoordinates) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometres."""
    lat1, lon1 = origin
    lat2, lon2 = destination

    radians_lat1 = math.radians(lat1)
    radians_lat2 = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(radians_lat1) * math.cos(radians_lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    earth_radius_km = 6371.0
    return earth_radius_km * c


def _listing_coordinates(listing: Dict[str, Any]) -> Optional[PostalCoordinates]:
    """Extract coordinates for a listing from its structured detail data."""
    details = listing.get("details") or {}
    location = details.get("location") or {}

    postal_code = location.get("zip") or location.get("postal_code")
    if isinstance(postal_code, str):
        coords = resolve_postal_code_coordinates(postal_code)
        if coords:
            return coords

    # Fallback: attempt to resolve the human-readable location string
    human_location = listing.get("location") or location.get("city") or ""
    if isinstance(human_location, str) and human_location.strip():
        return resolve_location_coordinates(human_location)

    return None


@dataclass(slots=True)
class LocationFilterStats:
    """Result statistics for location-based filtering."""

    origin_coordinates: Optional[PostalCoordinates]
    excluded_count: int
    missing_count: int
    kept_count: int
    radius_km: Optional[float]
    excluded_ids: List[str]
    missing_ids: List[str]


def filter_listings_by_radius(
    listings: Sequence[Dict[str, Any]],
    location: str,
    radius_km: Optional[float],
) -> tuple[List[Dict[str, Any]], LocationFilterStats]:
    """
    Filter listings that fall outside of the given radius around a location.

    Args:
        listings: Listing dictionaries containing detail information.
        location: Origin location in free-text form (city, postal code, etc.).
        radius_km: Maximum allowed distance in kilometres. If None, no filtering occurs.

    Returns:
        Tuple of (filtered_list, filter_stats)
    """
    origin_coords = resolve_location_coordinates(location)
    if radius_km is None or radius_km <= 0 or origin_coords is None:
        stats = LocationFilterStats(
            origin_coordinates=origin_coords,
            excluded_count=0,
            missing_count=0,
            kept_count=len(listings),
            radius_km=radius_km,
            excluded_ids=[],
            missing_ids=[],
        )
        return list(listings), stats

    filtered: List[Dict[str, Any]] = []
    excluded_ids: List[str] = []
    missing_ids: List[str] = []

    for listing in listings:
        ad_id = str(listing.get("adid") or listing.get("id") or "")
        coords = _listing_coordinates(listing)

        if coords is None:
            missing_ids.append(ad_id)
            continue

        distance = _haversine_km(origin_coords, coords)

        if distance <= radius_km:
            listing_copy = dict(listing)
            listing_copy["distance_km"] = round(distance, 1)
            filtered.append(listing_copy)
        else:
            excluded_ids.append(ad_id)

    stats = LocationFilterStats(
        origin_coordinates=origin_coords,
        excluded_count=len(excluded_ids),
        missing_count=len(missing_ids),
        kept_count=len(filtered),
        radius_km=radius_km,
        excluded_ids=excluded_ids,
        missing_ids=missing_ids,
    )
    return filtered, stats
