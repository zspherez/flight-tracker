import logging
import uuid

import aiosqlite

from .config import DATA_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracked_flights (
    id              TEXT PRIMARY KEY,
    origin          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    travel_date     TEXT NOT NULL,
    flight_codes    TEXT NOT NULL,
    departure_time  TEXT NOT NULL,
    arrival_time    TEXT NOT NULL,
    stops           INTEGER NOT NULL DEFAULT 0,
    duration        INTEGER,
    adults          INTEGER NOT NULL DEFAULT 1,
    custom_baseline REAL,
    label           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(origin, destination, travel_date, flight_codes, departure_time)
);

CREATE TABLE IF NOT EXISTS search_configs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   TEXT NOT NULL REFERENCES tracked_flights(id) ON DELETE CASCADE,
    from_airports       TEXT NOT NULL,
    to_airports         TEXT NOT NULL,
    max_stops           TEXT NOT NULL DEFAULT 'NON_STOP',
    seat_type           TEXT NOT NULL DEFAULT 'ECONOMY',
    airlines            TEXT,
    layover_airports    TEXT,
    exclude_basic_economy INTEGER NOT NULL DEFAULT 1,
    adults              INTEGER NOT NULL DEFAULT 1,
    UNIQUE(tracked_flight_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   TEXT NOT NULL REFERENCES tracked_flights(id) ON DELETE CASCADE,
    price               REAL NOT NULL,
    checked_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_price_history_flight
    ON price_history(tracked_flight_id, checked_at);

CREATE TABLE IF NOT EXISTS notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   TEXT NOT NULL REFERENCES tracked_flights(id),
    message             TEXT NOT NULL,
    old_price           REAL NOT NULL,
    new_price           REAL NOT NULL,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    is_read             INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS device_tokens (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    token           TEXT NOT NULL UNIQUE,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


async def _migrate_int_to_uuid(db: aiosqlite.Connection) -> None:
    """Convert tracked_flights.id from INTEGER autoincrement to UUID hex.

    Idempotent — detects current shape via PRAGMA table_info. No-op on fresh
    deploys (table doesn't exist) and on already-migrated deploys (id is TEXT).
    Rewrites tracked_flight_id FKs in search_configs, price_history, and
    notifications to point at the new UUIDs.
    """
    cursor = await db.execute("PRAGMA table_info(tracked_flights)")
    cols = await cursor.fetchall()
    id_col = next((c for c in cols if c["name"] == "id"), None)
    if not id_col or id_col["type"].upper() != "INTEGER":
        return

    cursor = await db.execute("SELECT id FROM tracked_flights")
    old_ids = [r["id"] for r in await cursor.fetchall()]
    id_map = {old: uuid.uuid4().hex for old in old_ids}
    logger.info(f"Migrating {len(id_map)} tracked flights to UUID hex IDs")

    await db.execute("PRAGMA foreign_keys = OFF")
    try:
        await db.execute("ALTER TABLE tracked_flights RENAME TO _old_tracked_flights")
        await db.execute("ALTER TABLE search_configs RENAME TO _old_search_configs")
        await db.execute("ALTER TABLE price_history RENAME TO _old_price_history")
        await db.execute("ALTER TABLE notifications RENAME TO _old_notifications")

        await db.executescript(SCHEMA)

        cursor = await db.execute("SELECT * FROM _old_tracked_flights")
        for r in await cursor.fetchall():
            await db.execute(
                """INSERT INTO tracked_flights
                   (id, origin, destination, travel_date, flight_codes,
                    departure_time, arrival_time, stops, duration, adults,
                    custom_baseline, label, is_active, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_map[r["id"]], r["origin"], r["destination"], r["travel_date"],
                    r["flight_codes"], r["departure_time"], r["arrival_time"],
                    r["stops"], r["duration"], r["adults"],
                    r["custom_baseline"], r["label"], r["is_active"], r["created_at"],
                ),
            )

        cursor = await db.execute("SELECT * FROM _old_search_configs")
        for r in await cursor.fetchall():
            await db.execute(
                """INSERT INTO search_configs
                   (tracked_flight_id, from_airports, to_airports, max_stops,
                    seat_type, airlines, layover_airports, exclude_basic_economy, adults)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    id_map[r["tracked_flight_id"]], r["from_airports"], r["to_airports"],
                    r["max_stops"], r["seat_type"], r["airlines"],
                    r["layover_airports"], r["exclude_basic_economy"], r["adults"],
                ),
            )

        cursor = await db.execute("SELECT * FROM _old_price_history")
        for r in await cursor.fetchall():
            await db.execute(
                "INSERT INTO price_history (tracked_flight_id, price, checked_at) "
                "VALUES (?, ?, ?)",
                (id_map[r["tracked_flight_id"]], r["price"], r["checked_at"]),
            )

        cursor = await db.execute("SELECT * FROM _old_notifications")
        for r in await cursor.fetchall():
            await db.execute(
                """INSERT INTO notifications
                   (tracked_flight_id, message, old_price, new_price, created_at, is_read)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    id_map[r["tracked_flight_id"]], r["message"], r["old_price"],
                    r["new_price"], r["created_at"], r["is_read"],
                ),
            )

        await db.execute("DROP TABLE _old_notifications")
        await db.execute("DROP TABLE _old_price_history")
        await db.execute("DROP TABLE _old_search_configs")
        await db.execute("DROP TABLE _old_tracked_flights")
        await db.commit()
    finally:
        await db.execute("PRAGMA foreign_keys = ON")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = await get_db()
    try:
        await _migrate_int_to_uuid(db)
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()
