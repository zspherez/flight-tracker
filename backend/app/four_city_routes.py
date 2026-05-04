"""
4-city route enumeration with live flight data.

Charleston (CHS) is REQUIRED. Choose 3 from {NYC, BNA, ORD, AUS}.
Refreshes via APScheduler; results cached in SQLite. Frontend re-applies
user-defined MCTs against gaps + connection inner-layovers; this module
only filters with a permissive BASELINE_MCT during enumeration to keep
the search space tractable.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from itertools import combinations, permutations

from .database import get_db
from .search import _run_search_multi_airport

logger = logging.getLogger(__name__)


NYC_AIRPORTS = {"LGA", "JFK", "EWR"}
CHICAGO_AIRPORTS = {"ORD", "MDW"}

CITY_AIRPORTS: dict[str, list[str]] = {
    "NYC": sorted(NYC_AIRPORTS),
    "CHS": ["CHS"],
    "ORD": sorted(CHICAGO_AIRPORTS),
    "AUS": ["AUS"],
    "BNA": ["BNA"],
}

# Permissive baseline used during enumeration (frontend re-filters per user MCT).
BASELINE_MCT = 30


def get_city_from_airport(code: str) -> str:
    if code in NYC_AIRPORTS:
        return "NYC"
    if code in CHICAGO_AIRPORTS:
        return "ORD"
    return code


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s)


def _fetch_all_flights(travel_date: str):
    """Synchronous: query fli for every cross-city pair (single-leg + 1-stop)."""
    flights_by_origin: dict[str, list[dict]] = {city: [] for city in CITY_AIRPORTS}
    connections: dict[tuple, list[dict]] = defaultdict(list)
    seen_direct: set = set()
    seen_conn: set = set()

    cities = list(CITY_AIRPORTS.keys())
    for orig_city in cities:
        for dest_city in cities:
            if orig_city == dest_city:
                continue

            try:
                results = _run_search_multi_airport(
                    from_airports=CITY_AIRPORTS[orig_city],
                    to_airports=CITY_AIRPORTS[dest_city],
                    travel_date=travel_date,
                    max_stops="ONE_STOP_OR_FEWER",
                    seat_type="ECONOMY",
                    airlines=None,
                    layover_airports=None,
                    exclude_basic_economy=True,
                )
            except Exception as e:
                logger.error(f"Search {orig_city}→{dest_city} failed: {e}")
                continue

            for r in results:
                if r.stops == 0 and len(r.legs) == 1:
                    leg = r.legs[0]
                    key = (
                        leg.departure_airport,
                        leg.arrival_airport,
                        leg.departure_datetime,
                        leg.flight_number,
                    )
                    if key in seen_direct:
                        continue
                    seen_direct.add(key)

                    flights_by_origin[orig_city].append({
                        "origin": leg.departure_airport,
                        "destination": leg.arrival_airport,
                        "departure": leg.departure_datetime,
                        "arrival": leg.arrival_datetime,
                        "carrier": leg.airline,
                        "flight_number": leg.flight_number,
                        "duration": leg.duration,
                        "price": r.price,
                        "is_connection": False,
                    })

                elif r.stops == 1 and len(r.legs) == 2:
                    leg1, leg2 = r.legs
                    stop_code = leg1.arrival_airport
                    stop_city = get_city_from_airport(stop_code)
                    actual_orig_city = get_city_from_airport(leg1.departure_airport)
                    actual_dest_city = get_city_from_airport(leg2.arrival_airport)

                    if stop_city == actual_orig_city or stop_city == actual_dest_city:
                        continue

                    key = (
                        leg1.departure_airport,
                        stop_code,
                        leg2.arrival_airport,
                        leg1.departure_datetime,
                        leg1.flight_number,
                        leg2.flight_number,
                    )
                    if key in seen_conn:
                        continue
                    seen_conn.add(key)

                    stop_layover = int(
                        (_parse_iso(leg2.departure_datetime) - _parse_iso(leg1.arrival_datetime)).total_seconds() / 60
                    )
                    if stop_layover < BASELINE_MCT:
                        continue

                    connections[(actual_orig_city, stop_city, actual_dest_city)].append({
                        "origin": leg1.departure_airport,
                        "stop": stop_code,
                        "destination": leg2.arrival_airport,
                        "departure": leg1.departure_datetime,
                        "arrival": leg2.arrival_datetime,
                        "stop_arrival": leg1.arrival_datetime,
                        "stop_departure": leg2.departure_datetime,
                        "stop_layover": stop_layover,
                        "carrier": leg1.airline,
                        "flight_number": f"{leg1.flight_number}, {leg2.flight_number}",
                        "duration": r.duration,
                        "price": r.price,
                        "is_connection": True,
                        "origin_city": actual_orig_city,
                        "stop_city": stop_city,
                        "dest_city": actual_dest_city,
                    })

    return flights_by_origin, dict(connections)


def _gap_minutes(b1: dict, b2: dict) -> int:
    return int((_parse_iso(b2["departure"]) - _parse_iso(b1["arrival"])).total_seconds() / 60)


def _is_valid_inter_booking(b1: dict, b2: dict, baseline_mct: int) -> tuple[bool, int]:
    """Time-order check between two separate bookings (same metro area)."""
    if get_city_from_airport(b1["destination"]) != get_city_from_airport(b2["origin"]):
        return False, 0
    gap = _gap_minutes(b1, b2)
    return gap >= baseline_mct, gap


def _find_for_route(route_cities, flights_by_origin, connections, relaxed):
    solutions = []
    last_idx = len(route_cities) - 1

    def get_direct(from_city, to_city):
        if from_city not in flights_by_origin:
            return []
        from_set = set(CITY_AIRPORTS[from_city])
        to_set = set(CITY_AIRPORTS[to_city])
        return [
            f for f in flights_by_origin[from_city]
            if f["origin"] in from_set and f["destination"] in to_set
        ]

    def get_conns(from_city, stop_city, to_city):
        return connections.get((from_city, stop_city, to_city), [])

    def build(idx, current, total_price):
        if idx == last_idx:
            first = current[0]
            last = current[-1]
            first_dep = _parse_iso(first["departure"])
            last_arr = _parse_iso(last["arrival"])

            if not relaxed and first_dep.hour < 9:
                return

            if last_arr.date() > first_dep.date() and last_arr.hour >= 4:
                return

            gaps = [_gap_minutes(current[i], current[i + 1]) for i in range(len(current) - 1)]

            solutions.append({
                "route": route_cities,
                "bookings": current,
                "gaps": gaps,
                "total_price": total_price,
                "departure_time": first["departure"],
                "arrival_time": last["arrival"],
                "relaxed": relaxed,
            })
            return

        cur_city = route_cities[idx]
        next_city = route_cities[idx + 1]

        for f in get_direct(cur_city, next_city):
            if current:
                ok, _ = _is_valid_inter_booking(current[-1], f, BASELINE_MCT)
                if not ok:
                    continue
            build(idx + 1, current + [f], total_price + f["price"])

        if idx + 2 <= last_idx:
            skip = route_cities[idx + 1]
            after = route_cities[idx + 2]
            for c in get_conns(cur_city, skip, after):
                if current:
                    ok, _ = _is_valid_inter_booking(current[-1], c, BASELINE_MCT)
                    if not ok:
                        continue
                build(idx + 2, current + [c], total_price + c["price"])

    build(0, [], 0.0)
    return solutions


def _find_routes(flights_by_origin: dict, connections: dict) -> list[dict]:
    valid = []
    other = ["NYC", "BNA", "ORD", "AUS"]

    for combo in combinations(other, 3):
        cities = ["CHS"] + list(combo)
        for perm in permutations(cities):
            valid.extend(_find_for_route(list(perm), flights_by_origin, connections, relaxed=False))

    return valid


CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS four_city_routes_cache (
    id              INTEGER PRIMARY KEY CHECK (id = 1),
    travel_date     TEXT NOT NULL,
    solutions_json  TEXT NOT NULL,
    refreshed_at    TEXT NOT NULL
);
"""


async def init_cache_table():
    db = await get_db()
    try:
        await db.execute(CACHE_TABLE_SQL)
        await db.commit()
    finally:
        await db.close()


async def refresh_routes(travel_date: str):
    """Fetch flights via fli, enumerate routes, cache to DB."""
    logger.info(f"Refreshing 4-city routes for {travel_date}")
    flights_by_origin, connections = await asyncio.to_thread(_fetch_all_flights, travel_date)
    solutions = _find_routes(flights_by_origin, connections)

    payload = json.dumps(solutions)
    refreshed = datetime.now().isoformat()

    db = await get_db()
    try:
        await db.execute(
            "INSERT OR REPLACE INTO four_city_routes_cache "
            "(id, travel_date, solutions_json, refreshed_at) VALUES (1, ?, ?, ?)",
            (travel_date, payload, refreshed),
        )
        await db.commit()
    finally:
        await db.close()

    logger.info(f"Cached {len(solutions)} 4-city solutions at {refreshed}")


async def get_cached_routes() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT travel_date, solutions_json, refreshed_at "
            "FROM four_city_routes_cache WHERE id = 1"
        )
        row = await cursor.fetchone()
        if not row:
            return {"travel_date": None, "solutions": [], "refreshed_at": None}
        return {
            "travel_date": row["travel_date"],
            "solutions": json.loads(row["solutions_json"]),
            "refreshed_at": row["refreshed_at"],
        }
    finally:
        await db.close()
