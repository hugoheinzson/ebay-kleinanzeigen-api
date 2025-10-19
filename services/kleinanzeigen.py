from typing import Optional

from scrapers.inserate import get_inserate_klaz_optimized
from scrapers.inserat import get_inserate_details_optimized
from utils.browser import OptimizedPlaywrightManager


async def fetch_listings(
    browser_manager: OptimizedPlaywrightManager,
    query: Optional[str] = None,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    page_count: int = 1,
):
    """Fetch listings using the optimized scraper with shared browser manager."""
    response = await get_inserate_klaz_optimized(
        browser_manager,
        query,
        location,
        radius,
        min_price,
        max_price,
        page_count,
    )
    return response


async def fetch_listing_details(
    browser_manager: OptimizedPlaywrightManager,
    listing_id: str
):
    """Fetch listing details using the optimized scraper with shared browser manager."""
    # FIXED: Use correct parameter order - browser_manager first, then listing_id
    return await get_inserate_details_optimized(browser_manager, listing_id)
