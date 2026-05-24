import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import POLL_INTERVAL_MINUTES
from .database import init_db
from .four_city_routes import init_cache_table
from .rate_limit import limiter
from .routers import flights, four_city, history, search
from .scheduler import check_all_prices

logging.basicConfig(level=logging.INFO)


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
    scheduler.start()
    logging.info(f"Scheduler started (price every {POLL_INTERVAL_MINUTES} min)")
    yield
    scheduler.shutdown()


app = FastAPI(title="Flight Price Tracker", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://flights.rehde.rs", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(flights.router)
app.include_router(history.router)
app.include_router(four_city.router)
