"""Background scheduler that periodically checks prices for all tracked flights."""

import json
import logging

from .database import get_db
from .notifier import send_push
from .search import search_flights_multi

logger = logging.getLogger(__name__)


async def check_all_prices():
    """Query all active tracked flights, group by search config, fetch prices."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """SELECT tf.id, tf.flight_codes, tf.departure_time, tf.travel_date,
                      sc.from_airports, sc.to_airports, sc.max_stops, sc.seat_type,
                      sc.airlines, sc.layover_airports, sc.exclude_basic_economy
               FROM tracked_flights tf
               JOIN search_configs sc ON sc.tracked_flight_id = tf.id
               WHERE tf.is_active = 1"""
        )
        rows = await cursor.fetchall()
    finally:
        await db.close()

    if not rows:
        return

    # Group flights by search config to deduplicate API calls
    groups: dict[str, dict] = {}
    for row in rows:
        key = (
            f"{row['from_airports']}|{row['to_airports']}|{row['travel_date']}|"
            f"{row['max_stops']}|{row['seat_type']}|{row['airlines']}|"
            f"{row['layover_airports']}|{row['exclude_basic_economy']}"
        )
        if key not in groups:
            groups[key] = {
                "config": row,
                "flights": [],
            }
        groups[key]["flights"].append(row)

    logger.info(f"Checking {len(rows)} flights in {len(groups)} search groups")

    for group in groups.values():
        config = group["config"]
        tracked = group["flights"]

        try:
            results = await search_flights_multi(
                from_airports=json.loads(config["from_airports"]),
                to_airports=json.loads(config["to_airports"]),
                travel_date=config["travel_date"],
                max_stops=config["max_stops"],
                seat_type=config["seat_type"],
                airlines=json.loads(config["airlines"]) if config["airlines"] else None,
                layover_airports=json.loads(config["layover_airports"]) if config["layover_airports"] else None,
                exclude_basic_economy=bool(config["exclude_basic_economy"]),
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            continue

        # Match results to tracked flights by flight_codes + departure_time
        result_lookup = {}
        for r in results:
            # Match on first-leg code + departure time (same as monitor_prices.py)
            first_code = r.legs[0].airline + r.legs[0].flight_number if r.legs else ""
            result_lookup[(first_code, r.departure_time)] = r
            # Also index by full flight_codes for exact match
            result_lookup[(r.flight_codes, r.departure_time)] = r

        db = await get_db()
        try:
            for flight in tracked:
                codes = flight["flight_codes"]
                dep = flight["departure_time"]
                first_code = codes.split("/")[0]

                matched = (
                    result_lookup.get((first_code, dep))
                    or result_lookup.get((codes, dep))
                )

                if not matched:
                    logger.warning(f"Flight {codes} dep {dep} not found in results")
                    continue

                new_price = matched.price

                # Get previous minimum
                cursor = await db.execute(
                    "SELECT MIN(price) as min_price FROM price_history "
                    "WHERE tracked_flight_id = ?",
                    (flight["id"],),
                )
                min_row = await cursor.fetchone()
                old_min = min_row["min_price"] if min_row and min_row["min_price"] is not None else None

                # Record price
                await db.execute(
                    "INSERT INTO price_history (tracked_flight_id, price) VALUES (?, ?)",
                    (flight["id"], new_price),
                )

                # Create notification on new all-time low
                if old_min is not None and new_price < old_min:
                    msg = (
                        f"{flight['flight_codes']} dropped to ${new_price:.2f} "
                        f"(was ${old_min:.2f}, -${old_min - new_price:.2f})"
                    )
                    await db.execute(
                        "INSERT INTO notifications "
                        "(tracked_flight_id, message, old_price, new_price) "
                        "VALUES (?, ?, ?, ?)",
                        (flight["id"], msg, old_min, new_price),
                    )
                    logger.info(f"Price drop: {msg}")
                    await send_push("Flight Price Drop!", msg)

            await db.commit()
        finally:
            await db.close()

    logger.info("Price check complete")
