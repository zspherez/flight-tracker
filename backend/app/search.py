"""Wrapper around the fli library for flight searching."""

import asyncio

from fli.models import (
    Airport,
    Airline,
    FlightSearchFilters,
    FlightSegment,
    LayoverRestrictions,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
    TimeRestrictions,
    TripType,
)
from fli.search import SearchFlights

from .models import FlightResultResponse, LegResponse, SearchRequest

# Spirit excluded globally
EXCLUDED_AIRLINES = {"NK"}


def _resolve_airport(code: str) -> Airport:
    return getattr(Airport, code.upper())


def _resolve_airline(code: str) -> Airline:
    return getattr(Airline, code.upper())


def _resolve_max_stops(s: str) -> MaxStops:
    return MaxStops[s.upper()]


def _resolve_seat_type(s: str) -> SeatType:
    return SeatType[s.upper()]


def _run_search(params: SearchRequest) -> list[FlightResultResponse]:
    """Synchronous fli search — called via asyncio.to_thread."""
    time_restrictions = None
    if params.departure_from is not None or params.departure_to is not None:
        time_restrictions = TimeRestrictions(
            earliest_departure=params.departure_from,
            latest_departure=params.departure_to,
        )

    segment = FlightSegment(
        departure_airport=[[_resolve_airport(a), 0] for a in [params.origin]],
        arrival_airport=[[_resolve_airport(a), 0] for a in [params.destination]],
        travel_date=params.travel_date,
        time_restrictions=time_restrictions,
    )

    layover = None
    if params.layover_airports:
        layover = LayoverRestrictions(
            airports=[_resolve_airport(a) for a in params.layover_airports]
        )

    airlines = None
    if params.airlines:
        airlines = [_resolve_airline(a) for a in params.airlines]

    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=params.adults),
        flight_segments=[segment],
        stops=_resolve_max_stops(params.max_stops),
        seat_type=_resolve_seat_type(params.seat_type),
        sort_by=SortBy.CHEAPEST,
        exclude_basic_economy=params.exclude_basic_economy,
        airlines=airlines,
        layover_restrictions=layover,
    )

    results = SearchFlights().search(filters)

    # Filter out Spirit
    results = [
        r for r in results
        if not any(leg.airline.name in EXCLUDED_AIRLINES for leg in r.legs)
    ]

    out = []
    for r in results:
        first_leg = r.legs[0]
        last_leg = r.legs[-1]
        codes = "/".join(f"{l.airline.name}{l.flight_number}" for l in r.legs)

        legs = [
            LegResponse(
                airline=l.airline.name,
                flight_number=l.flight_number,
                departure_airport=l.departure_airport.name,
                arrival_airport=l.arrival_airport.name,
                departure_datetime=l.departure_datetime.isoformat(),
                arrival_datetime=l.arrival_datetime.isoformat(),
                duration=l.duration,
            )
            for l in r.legs
        ]

        out.append(FlightResultResponse(
            origin=first_leg.departure_airport.name,
            destination=last_leg.arrival_airport.name,
            flight_codes=codes,
            departure_time=first_leg.departure_datetime.strftime("%H:%M"),
            arrival_time=last_leg.arrival_datetime.strftime("%H:%M"),
            price=r.price,
            stops=r.stops,
            duration=r.duration,
            legs=legs,
        ))

    return out


def _run_search_multi_airport(
    from_airports: list[str],
    to_airports: list[str],
    travel_date: str,
    max_stops: str,
    seat_type: str,
    airlines: list[str] | None,
    layover_airports: list[str] | None,
    exclude_basic_economy: bool,
) -> list[FlightResultResponse]:
    """Synchronous search with explicit multi-airport support (for scheduler)."""
    segment = FlightSegment(
        departure_airport=[[_resolve_airport(a), 0] for a in from_airports],
        arrival_airport=[[_resolve_airport(a), 0] for a in to_airports],
        travel_date=travel_date,
    )

    layover = None
    if layover_airports:
        layover = LayoverRestrictions(
            airports=[_resolve_airport(a) for a in layover_airports]
        )

    parsed_airlines = None
    if airlines:
        parsed_airlines = [_resolve_airline(a) for a in airlines]

    filters = FlightSearchFilters(
        trip_type=TripType.ONE_WAY,
        passenger_info=PassengerInfo(adults=1),
        flight_segments=[segment],
        stops=_resolve_max_stops(max_stops),
        seat_type=_resolve_seat_type(seat_type),
        sort_by=SortBy.CHEAPEST,
        exclude_basic_economy=exclude_basic_economy,
        airlines=parsed_airlines,
        layover_restrictions=layover,
    )

    results = SearchFlights().search(filters)
    results = [
        r for r in results
        if not any(leg.airline.name in EXCLUDED_AIRLINES for leg in r.legs)
    ]

    out = []
    for r in results:
        first_leg = r.legs[0]
        last_leg = r.legs[-1]
        codes = "/".join(f"{l.airline.name}{l.flight_number}" for l in r.legs)

        legs = [
            LegResponse(
                airline=l.airline.name,
                flight_number=l.flight_number,
                departure_airport=l.departure_airport.name,
                arrival_airport=l.arrival_airport.name,
                departure_datetime=l.departure_datetime.isoformat(),
                arrival_datetime=l.arrival_datetime.isoformat(),
                duration=l.duration,
            )
            for l in r.legs
        ]

        out.append(FlightResultResponse(
            origin=first_leg.departure_airport.name,
            destination=last_leg.arrival_airport.name,
            flight_codes=codes,
            departure_time=first_leg.departure_datetime.strftime("%H:%M"),
            arrival_time=last_leg.arrival_datetime.strftime("%H:%M"),
            price=r.price,
            stops=r.stops,
            duration=r.duration,
            legs=legs,
        ))

    return out


async def search_flights(params: SearchRequest) -> list[FlightResultResponse]:
    return await asyncio.to_thread(_run_search, params)


async def search_flights_multi(
    from_airports: list[str],
    to_airports: list[str],
    travel_date: str,
    max_stops: str,
    seat_type: str,
    airlines: list[str] | None,
    layover_airports: list[str] | None,
    exclude_basic_economy: bool,
) -> list[FlightResultResponse]:
    return await asyncio.to_thread(
        _run_search_multi_airport,
        from_airports, to_airports, travel_date,
        max_stops, seat_type, airlines, layover_airports,
        exclude_basic_economy,
    )


def get_airport_codes() -> list[dict]:
    """Return all airport codes for autocomplete."""
    return [{"code": a.name, "name": a.value} for a in Airport]
