import os
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from services.kleinanzeigen import fetch_listing_details, fetch_listings
from utils.browser import OptimizedPlaywrightManager


# Global browser manager for MCP server
_browser_manager: Optional[OptimizedPlaywrightManager] = None


async def get_browser_manager() -> OptimizedPlaywrightManager:
    """Get or create the shared browser manager for MCP tools."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = OptimizedPlaywrightManager(max_contexts=10, max_concurrent=5)
        await _browser_manager.start()
    return _browser_manager


def create_mcp_server(host: Optional[str] = None, port: Optional[int] = None) -> FastMCP:
    resolved_host = host or os.getenv("MCP_HOST", "0.0.0.0")
    resolved_port = port if port is not None else int(os.getenv("MCP_PORT", "8001"))

    server = FastMCP(
        name="Kleinanzeigen MCP",
        instructions="Tools for searching Kleinanzeigen listings and fetching listing details with optimized performance.",
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
            browser_manager = await get_browser_manager()
            response = await fetch_listings(
                browser_manager, query, location, radius, min_price, max_price, page_count
            )
            
            # Extract just the results for MCP response
            if response.get("success"):
                return {
                    "success": True,
                    "data": response.get("data", []),
                    "time_taken": response.get("time_taken", 0),
                    "unique_results": response.get("unique_results", 0)
                }
            else:
                return response
        except Exception as exc:
            raise RuntimeError(f"Failed to search listings: {exc}") from exc

    @server.tool(
        name="get_listing_details",
        description="Fetch detailed information for a Kleinanzeigen listing by its ID.",
    )
    async def get_listing_details(listing_id: str) -> dict:
        if not listing_id:
            raise ValueError("listing_id is required")

        try:
            browser_manager = await get_browser_manager()
            result = await fetch_listing_details(browser_manager, listing_id)
            return {"success": True, "data": result}
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch listing details: {exc}") from exc

    return server


if __name__ == "__main__":
    create_mcp_server().run("streamable-http")
