from fastapi import APIRouter

from ..config import FOUR_CITY_TRAVEL_DATE
from ..four_city_routes import get_cached_routes, refresh_routes

router = APIRouter(prefix="/api/four-city", tags=["four-city"])


@router.get("/routes")
async def get_routes():
    """Return cached enumerated 4-city solutions plus refresh metadata.

    Frontend re-applies user-defined MCTs against `gaps[i]` (gap between
    bookings i and i+1, at the airport `bookings[i].destination`) and
    `bookings[j].stop_layover` (inner connection layover at `bookings[j].stop`).
    """
    return await get_cached_routes()


@router.post("/refresh")
async def force_refresh():
    """Trigger an immediate refresh."""
    await refresh_routes(FOUR_CITY_TRAVEL_DATE)
    return await get_cached_routes()
