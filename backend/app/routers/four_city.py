from fastapi import APIRouter, Query, Request

from ..config import FOUR_CITY_TRAVEL_DATE
from ..four_city_routes import get_cached_routes, refresh_routes
from ..rate_limit import FLI_BOUND, limiter

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
@limiter.limit(FLI_BOUND)
async def force_refresh(
    request: Request,
    travel_date: str = Query(default=FOUR_CITY_TRAVEL_DATE, regex=r"^\d{4}-\d{2}-\d{2}$"),
):
    """Trigger an immediate refresh. Pass ?travel_date=YYYY-MM-DD to override."""
    await refresh_routes(travel_date)
    return await get_cached_routes()
