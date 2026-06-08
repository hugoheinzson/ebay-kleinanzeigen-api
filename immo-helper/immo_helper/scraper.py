import asyncio
import re
from typing import Any, Dict, List, Optional

from playwright.async_api import Page, async_playwright


async def scrape_listing(url: str) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Dismiss cookie banner if present
            try:
                await page.click("#gdpr-banner-accept", timeout=3000)
                await page.wait_for_timeout(500)
            except Exception:
                pass
            return await _extract(page, url)
        finally:
            await browser.close()


async def _extract(page: Page, url: str) -> Dict[str, Any]:
    ad_id = await _text(page, "#viewad-ad-id-box > ul > li:nth-child(2)")
    title_raw = await _text(page, "#viewad-title")
    title = title_raw.split(" • ")[-1].strip() if " • " in title_raw else title_raw.strip()
    price_text = await _text(page, "#viewad-price")
    description = await _text(page, "#viewad-description-text")
    if description:
        description = re.sub(r"[ \t]+", " ", description).strip()
        description = re.sub(r"\n{3,}", "\n\n", description)
    location_text = await _text(page, "#viewad-locality")
    created_at = await _text(page, "#viewad-extra-info > div:nth-child(1) > span")
    details = await _details(page)
    images = await _all_images(page)
    return {
        "id": ad_id.strip(),
        "url": url,
        "title": title,
        "price": _parse_price(price_text),
        "location": _parse_location(location_text),
        "description": description,
        "details": details,
        "images": images,
        "created_at": created_at.strip(),
    }


async def _all_images(page: Page) -> List[str]:
    images: List[str] = []
    # Gallery thumbnails contain all listing photos
    thumbnail_selectors = [
        "#viewad-thumbnails img",
        ".galleryimage-element img",
        "#viewad-image-big img",
        ".imagebox-stretch img",
        "#viewad-gallery img",
    ]
    for selector in thumbnail_selectors:
        elements = await page.query_selector_all(selector)
        for el in elements:
            src = await el.get_attribute("src") or await el.get_attribute("data-src") or ""
            src = src.strip()
            if src and "placeholder" not in src.lower() and src not in images:
                images.append(_upscale_url(src))
    # Fallback to single main image
    if not images:
        el = await page.query_selector("#viewad-image img, #viewad-image")
        if el:
            src = await el.get_attribute("src") or ""
            if src:
                images.append(_upscale_url(src))
    return images


def _upscale_url(url: str) -> str:
    # eBay image CDN uses sizes like s-l400, s-l640 → upgrade to s-l1600
    return re.sub(r"s-l\d+", "s-l1600", url)


async def _text(page: Page, selector: str) -> str:
    el = await page.query_selector(selector)
    return (await el.inner_text()) if el else ""


async def _details(page: Page) -> Dict[str, str]:
    result: Dict[str, str] = {}
    try:
        items = await page.query_selector_all("#viewad-details .addetailslist--detail")
        for item in items:
            content = await item.text_content() or ""
            val_el = await item.query_selector(".addetailslist--detail--value")
            if val_el:
                val = (await val_el.text_content() or "").strip()
                label = content.replace(val, "").strip()
                result[label] = val
    except Exception:
        pass
    return result


def _parse_price(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    negotiable = "VB" in text
    clean = text.replace("VB", "").replace("€", "").replace(".", "").replace(",", ".").strip()
    try:
        amount: Optional[float] = float(clean)
    except ValueError:
        amount = None
    return {"amount": amount, "currency": "€", "negotiable": negotiable, "raw": text}


def _parse_location(text: str) -> Dict[str, str]:
    text = (text or "").strip()
    if not text:
        return {"zip": "", "city": "", "full": ""}
    parts = text.split(" - ") if " - " in text else [text]
    first_parts = parts[0].strip().split(" ", 1)
    zip_code = first_parts[0] if first_parts else ""
    city = parts[1].strip() if len(parts) > 1 else (first_parts[1] if len(first_parts) > 1 else "")
    return {"zip": zip_code, "city": city, "full": text}
