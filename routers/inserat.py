from fastapi import APIRouter

from services.kleinanzeigen import fetch_listing_details

router = APIRouter()

@router.get("/inserat/{id}")
async def get_inserat(id: str):
    result = await fetch_listing_details(id)
    return {"success": True, "data": result}