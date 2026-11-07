import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fli.search.exceptions import SearchClientError
from pydantic import ValidationError

from ..models import FlightResultResponse, SearchRequest
from ..rate_limit import FLI_BOUND, limiter
from ..search import get_airport_codes, search_flights

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)


@router.post("/search", response_model=list[FlightResultResponse])
@limiter.limit(FLI_BOUND)
async def search(request: Request, params: SearchRequest):
    try:
        return await search_flights(params)
    except ValidationError as exc:
        logger.warning("Invalid flight search: %s", exc)
        raise HTTPException(422, detail=str(exc)) from exc
    except SearchClientError as exc:
        logger.exception("Google Flights search failed")
        raise HTTPException(
            502, detail="Google Flights could not return results. Please try again later."
        ) from exc


@router.get("/airports")
async def airports(q: str = Query("", min_length=1)):
    q = q.upper()
    all_airports = get_airport_codes()
    return [
        a for a in all_airports
        if q in a["code"] or q in a["name"].upper()
    ][:20]
