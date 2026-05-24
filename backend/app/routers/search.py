from fastapi import APIRouter, Query, Request

from ..models import FlightResultResponse, SearchRequest
from ..rate_limit import FLI_BOUND, limiter
from ..search import get_airport_codes, search_flights

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/search", response_model=list[FlightResultResponse])
@limiter.limit(FLI_BOUND)
async def search(request: Request, params: SearchRequest):
    return await search_flights(params)


@router.get("/airports")
async def airports(q: str = Query("", min_length=1)):
    q = q.upper()
    all_airports = get_airport_codes()
    return [
        a for a in all_airports
        if q in a["code"] or q in a["name"].upper()
    ][:20]
