import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    FOUR_CITY_REFRESH_MINUTES,
    FOUR_CITY_TRAVEL_DATE,
    POLL_INTERVAL_MINUTES,
)
from .database import init_db
from .four_city_routes import init_cache_table, refresh_routes
from .routers import flights, four_city, history, search
from .scheduler import check_all_prices

logging.basicConfig(level=logging.INFO)


async def _refresh_four_city():
    await refresh_routes(FOUR_CITY_TRAVEL_DATE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_cache_table()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_all_prices,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="price_checker",
    )
    scheduler.add_job(
        _refresh_four_city,
        "interval",
        minutes=FOUR_CITY_REFRESH_MINUTES,
        id="four_city_refresher",
        next_run_time=datetime.now() + timedelta(seconds=15),
    )
    scheduler.start()
    logging.info(
        f"Scheduler started (price every {POLL_INTERVAL_MINUTES} min, "
        f"4-city every {FOUR_CITY_REFRESH_MINUTES} min)"
    )
    yield
    scheduler.shutdown()


app = FastAPI(title="Flight Price Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(flights.router)
app.include_router(history.router)
app.include_router(four_city.router)
