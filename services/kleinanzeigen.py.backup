from typing import Optional

from scrapers.inserate import get_inserate_klaz
from scrapers.inserat import get_inserate_details
from utils.browser import PlaywrightManager


async def fetch_listings(
    query: Optional[str] = None,
    location: Optional[str] = None,
    radius: Optional[int] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    page_count: int = 1,
):
    browser_manager = PlaywrightManager()
    await browser_manager.start()
    try:
        results = await get_inserate_klaz(
            browser_manager,
            query,
            location,
            radius,
            min_price,
            max_price,
            page_count,
        )
        return results
    finally:
        await browser_manager.close()


async def fetch_listing_details(listing_id: str):
    browser_manager = PlaywrightManager()
    await browser_manager.start()
    try:
        page = await browser_manager.new_context_page()
        url = f"https://www.kleinanzeigen.de/s-anzeige/{listing_id}"
        return await get_inserate_details(url, page)
    finally:
        await browser_manager.close()
