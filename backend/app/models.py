from pydantic import BaseModel


class LegResponse(BaseModel):
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_datetime: str
    arrival_datetime: str
    duration: int


class FlightResultResponse(BaseModel):
    origin: str
    destination: str
    flight_codes: str
    departure_time: str
    arrival_time: str
    price: float
    stops: int
    duration: int
    legs: list[LegResponse]


class SearchRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str
    max_stops: str = "ANY"
    adults: int = 1
    seat_type: str = "ECONOMY"
    airlines: list[str] | None = None
    layover_airports: list[str] | None = None
    exclude_basic_economy: bool = True


class TrackFlightRequest(BaseModel):
    origin: str
    destination: str
    travel_date: str
    flight_codes: str
    departure_time: str
    arrival_time: str
    stops: int
    duration: int | None = None
    label: str | None = None
    price: float
    search_from_airports: list[str]
    search_to_airports: list[str]
    search_max_stops: str = "NON_STOP"
    search_seat_type: str = "ECONOMY"
    search_airlines: list[str] | None = None
    search_layover_airports: list[str] | None = None


class TrackedFlightResponse(BaseModel):
    id: int
    origin: str
    destination: str
    travel_date: str
    flight_codes: str
    departure_time: str
    arrival_time: str
    stops: int
    duration: int | None
    label: str | None
    is_active: bool
    created_at: str
    latest_price: float | None
    baseline_price: float | None
    price_change: float | None


class PriceHistoryPoint(BaseModel):
    price: float
    checked_at: str


class NotificationResponse(BaseModel):
    id: int
    tracked_flight_id: int
    message: str
    old_price: float
    new_price: float
    created_at: str
    is_read: bool
