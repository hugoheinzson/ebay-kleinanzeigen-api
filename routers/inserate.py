from fastapi import APIRouter, Query

from services.kleinanzeigen import fetch_listings

router = APIRouter()


@router.get("/inserate")
async def get_inserate(query: str = Query(None),
                       location: str = Query(None),
                       radius: int = Query(None),
                       min_price: int = Query(None),
                       max_price: int = Query(None),
                       page_count: int = Query(1, ge=1, le=20)):
    results = await fetch_listings(query, location, radius, min_price, max_price, page_count)
    return {"success": True, "data": results}
