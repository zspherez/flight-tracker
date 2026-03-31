import json

from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models import TrackFlightRequest, TrackedFlightResponse

router = APIRouter(prefix="/api", tags=["flights"])


async def _build_response(row) -> TrackedFlightResponse:
    db = await get_db()
    try:
        # Latest price
        cursor = await db.execute(
            "SELECT price FROM price_history WHERE tracked_flight_id = ? "
            "ORDER BY checked_at DESC LIMIT 1",
            (row["id"],),
        )
        latest = await cursor.fetchone()
        latest_price = latest["price"] if latest else None

        # Baseline (all-time min)
        cursor = await db.execute(
            "SELECT MIN(price) as min_price FROM price_history WHERE tracked_flight_id = ?",
            (row["id"],),
        )
        baseline_row = await cursor.fetchone()
        baseline_price = baseline_row["min_price"] if baseline_row else None

        price_change = None
        if latest_price is not None and baseline_price is not None:
            price_change = latest_price - baseline_price

        return TrackedFlightResponse(
            id=row["id"],
            origin=row["origin"],
            destination=row["destination"],
            travel_date=row["travel_date"],
            flight_codes=row["flight_codes"],
            departure_time=row["departure_time"],
            arrival_time=row["arrival_time"],
            stops=row["stops"],
            duration=row["duration"],
            adults=row["adults"] if "adults" in row.keys() else 1,
            label=row["label"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            latest_price=latest_price,
            baseline_price=baseline_price,
            price_change=price_change,
        )
    finally:
        await db.close()


@router.get("/flights", response_model=list[TrackedFlightResponse])
async def list_flights():
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM tracked_flights ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()
    return [await _build_response(row) for row in rows]


@router.post("/flights", response_model=TrackedFlightResponse, status_code=201)
async def track_flight(req: TrackFlightRequest):
    db = await get_db()
    try:
        cursor = await db.execute(
            """INSERT INTO tracked_flights
               (origin, destination, travel_date, flight_codes,
                departure_time, arrival_time, stops, duration, adults, label)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                req.origin, req.destination, req.travel_date, req.flight_codes,
                req.departure_time, req.arrival_time, req.stops, req.duration,
                req.adults,
                req.label or f"{req.origin}→{req.destination} {req.flight_codes}",
            ),
        )
        flight_id = cursor.lastrowid

        await db.execute(
            """INSERT INTO search_configs
               (tracked_flight_id, from_airports, to_airports, max_stops,
                seat_type, airlines, layover_airports, exclude_basic_economy, adults)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                flight_id,
                json.dumps(req.search_from_airports),
                json.dumps(req.search_to_airports),
                req.search_max_stops,
                req.search_seat_type,
                json.dumps(req.search_airlines) if req.search_airlines else None,
                json.dumps(req.search_layover_airports) if req.search_layover_airports else None,
                1,
                req.adults,
            ),
        )

        # Record initial price
        await db.execute(
            "INSERT INTO price_history (tracked_flight_id, price) VALUES (?, ?)",
            (flight_id, req.price),
        )

        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM tracked_flights WHERE id = ?", (flight_id,)
        )
        row = await cursor.fetchone()
    finally:
        await db.close()

    return await _build_response(row)


@router.delete("/flights/{flight_id}", status_code=204)
async def delete_flight(flight_id: int):
    db = await get_db()
    try:
        await db.execute("DELETE FROM notifications WHERE tracked_flight_id = ?", (flight_id,))
        await db.execute("DELETE FROM price_history WHERE tracked_flight_id = ?", (flight_id,))
        await db.execute("DELETE FROM search_configs WHERE tracked_flight_id = ?", (flight_id,))
        cursor = await db.execute("DELETE FROM tracked_flights WHERE id = ?", (flight_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Flight not found")
    finally:
        await db.close()


@router.patch("/flights/{flight_id}", response_model=TrackedFlightResponse)
async def toggle_flight(flight_id: int):
    db = await get_db()
    try:
        await db.execute(
            "UPDATE tracked_flights SET is_active = 1 - is_active WHERE id = ?",
            (flight_id,),
        )
        await db.commit()
        cursor = await db.execute(
            "SELECT * FROM tracked_flights WHERE id = ?", (flight_id,)
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(404, "Flight not found")
    finally:
        await db.close()
    return await _build_response(row)
