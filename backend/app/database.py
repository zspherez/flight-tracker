import aiosqlite

from .config import DATA_DIR, DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracked_flights (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    origin          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    travel_date     TEXT NOT NULL,
    flight_codes    TEXT NOT NULL,
    departure_time  TEXT NOT NULL,
    arrival_time    TEXT NOT NULL,
    stops           INTEGER NOT NULL DEFAULT 0,
    duration        INTEGER,
    adults          INTEGER NOT NULL DEFAULT 1,
    label           TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(origin, destination, travel_date, flight_codes, departure_time)
);

CREATE TABLE IF NOT EXISTS search_configs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   INTEGER NOT NULL REFERENCES tracked_flights(id) ON DELETE CASCADE,
    from_airports       TEXT NOT NULL,
    to_airports         TEXT NOT NULL,
    max_stops           TEXT NOT NULL DEFAULT 'NON_STOP',
    seat_type           TEXT NOT NULL DEFAULT 'ECONOMY',
    airlines            TEXT,
    layover_airports    TEXT,
    exclude_basic_economy INTEGER NOT NULL DEFAULT 1,
    UNIQUE(tracked_flight_id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   INTEGER NOT NULL REFERENCES tracked_flights(id) ON DELETE CASCADE,
    price               REAL NOT NULL,
    checked_at          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_price_history_flight
    ON price_history(tracked_flight_id, checked_at);

CREATE TABLE IF NOT EXISTS notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tracked_flight_id   INTEGER NOT NULL REFERENCES tracked_flights(id),
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


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys = ON")
    return db


async def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.commit()
    finally:
        await db.close()
