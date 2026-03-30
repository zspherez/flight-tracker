import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import POLL_INTERVAL_MINUTES
from .database import init_db
from .routers import flights, history, search
from .scheduler import check_all_prices

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_all_prices,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="price_checker",
    )
    scheduler.start()
    logging.info(f"Scheduler started (every {POLL_INTERVAL_MINUTES} min)")
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
