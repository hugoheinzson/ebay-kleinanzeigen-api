"""Sync a scraped listing to a Notion database."""
import os
from typing import Any, Dict, List

from notion_client import AsyncClient


DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")


async def add_listing(listing: Dict[str, Any]) -> str:
    """Create a Notion page for the listing. Returns the Notion page URL."""
    client = AsyncClient(auth=os.environ["NOTION_TOKEN"])

    properties = _build_properties(listing)
    children = _build_content(listing)

    response = await client.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties,
        children=children,
        cover=_cover(listing),
    )
    return response.get("url", "")


def _build_properties(listing: Dict[str, Any]) -> Dict[str, Any]:
    price = listing["price"]
    loc = listing["location"]
    details = listing.get("details", {})

    props: Dict[str, Any] = {
        "Name": {"title": [{"text": {"content": listing["title"]}}]},
        "Status": {"select": {"name": "Neu"}},
        "Ort": {"rich_text": [{"text": {"content": loc["city"] or loc["full"]}}]},
        "URL": {"url": listing["url"]},
        "Anzeigen-ID": {"rich_text": [{"text": {"content": listing["id"]}}]},
    }

    if price["amount"] is not None:
        props["Preis"] = {"number": price["amount"]}

    # Try to extract Zimmer and Fläche from details
    for key, val in details.items():
        if "zimmer" in key.lower():
            try:
                props["Zimmer"] = {"number": float(val.replace(",", "."))}
            except ValueError:
                pass
        elif "fläche" in key.lower() or "wohnfläche" in key.lower():
            try:
                sqm = float(val.replace("m²", "").replace(",", ".").strip())
                props["Fläche"] = {"number": sqm}
            except ValueError:
                pass

    if listing.get("created_at"):
        # Notion date expects ISO format; created_at is a German text like "01.06.2026"
        iso = _parse_german_date(listing["created_at"])
        if iso:
            props["Eingestellt"] = {"date": {"start": iso}}

    return props


def _build_content(listing: Dict[str, Any]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []

    # Cover image already set, show all images as a gallery via image blocks
    for url in listing.get("images", [])[:10]:  # Notion allows up to 100 children per request
        blocks.append({
            "type": "image",
            "image": {"type": "external", "external": {"url": url}},
        })

    if listing.get("description"):
        blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Beschreibung"}}]}})
        # Split long descriptions into chunks (Notion limit: 2000 chars per block)
        desc = listing["description"]
        for chunk in _chunks(desc, 2000):
            blocks.append({
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
            })

    if listing.get("details"):
        blocks.append({"type": "heading_2", "heading_2": {"rich_text": [{"type": "text", "text": {"content": "Details"}}]}})
        for key, val in listing["details"].items():
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f"{key}: {val}"}}]},
            })

    return blocks


def _cover(listing: Dict[str, Any]) -> Dict[str, Any] | None:
    images = listing.get("images", [])
    if images:
        return {"type": "external", "external": {"url": images[0]}}
    return None


def _parse_german_date(text: str) -> str:
    """Convert 'TT.MM.JJJJ' to 'JJJJ-MM-TT'. Returns empty string on failure."""
    import re
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return ""


def _chunks(text: str, size: int):
    for i in range(0, len(text), size):
        yield text[i : i + size]
