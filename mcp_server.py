import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from services.kleinanzeigen import fetch_listing_details, fetch_listings


def create_mcp_server(host: Optional[str] = None, port: Optional[int] = None) -> FastMCP:
    resolved_host = host or os.getenv("MCP_HOST", "0.0.0.0")
    resolved_port = port if port is not None else int(os.getenv("MCP_PORT", "8001"))

    server = FastMCP(
        name="Kleinanzeigen MCP",
        instructions="Tools for searching Kleinanzeigen listings and fetching listing details.",
        host=resolved_host,
        port=resolved_port,
    )

    @server.tool(
        name="search_listings",
        description="Search Kleinanzeigen listings using query, location, price, and pagination filters.",
    )
    async def search_listings(
        query: Optional[str] = None,
        location: Optional[str] = None,
        radius: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        page_count: int = 1,
    ) -> dict:
        if page_count < 1 or page_count > 20:
            raise ValueError("page_count must be between 1 and 20")

        try:
            results = await fetch_listings(query, location, radius, min_price, max_price, page_count)
        except Exception as exc:  # pragma: no cover - bubble up tool error
            raise RuntimeError(f"Failed to search listings: {exc}") from exc
        return {"success": True, "data": results}

    @server.tool(
        name="get_listing_details",
        description="Fetch detailed information for a Kleinanzeigen listing by its ID.",
    )
    async def get_listing_details(listing_id: str) -> dict:
        if not listing_id:
            raise ValueError("listing_id is required")

        try:
            result = await fetch_listing_details(listing_id)
        except Exception as exc:  # pragma: no cover - bubble up tool error
            raise RuntimeError(f"Failed to fetch listing details: {exc}") from exc
        return {"success": True, "data": result}

    return server


if __name__ == "__main__":
    create_mcp_server().run("streamable-http")
