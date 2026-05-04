from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "flights.db"
POLL_INTERVAL_MINUTES = 1

# 4-city route finder
FOUR_CITY_TRAVEL_DATE = "2026-05-10"
FOUR_CITY_REFRESH_MINUTES = 30
