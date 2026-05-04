export interface Leg {
  airline: string;
  flight_number: string;
  departure_airport: string;
  arrival_airport: string;
  departure_datetime: string;
  arrival_datetime: string;
  duration: number;
}

export interface FlightResult {
  origin: string;
  destination: string;
  flight_codes: string;
  departure_time: string;
  arrival_time: string;
  price: number;
  stops: number;
  duration: number;
  legs: Leg[];
}

export interface SearchParams {
  origin: string;
  destination: string;
  travel_date: string;
  max_stops: string;
  adults?: number;
  seat_type?: string;
  airlines?: string[];
  layover_airports?: string[];
  departure_from?: number;
  departure_to?: number;
  exclude_basic_economy?: boolean;
}

export interface TrackedFlight {
  id: number;
  origin: string;
  destination: string;
  travel_date: string;
  flight_codes: string;
  departure_time: string;
  arrival_time: string;
  stops: number;
  duration: number | null;
  adults: number;
  label: string | null;
  is_active: boolean;
  created_at: string;
  latest_price: number | null;
  baseline_price: number | null;
  price_change: number | null;
}

export interface PricePoint {
  price: number;
  checked_at: string;
}

export interface Notification {
  id: number;
  tracked_flight_id: number;
  message: string;
  old_price: number;
  new_price: number;
  created_at: string;
  is_read: boolean;
}

export interface AirportOption {
  code: string;
  name: string;
}

export interface FourCityBooking {
  origin: string;
  destination: string;
  departure: string;
  arrival: string;
  carrier: string;
  flight_number: string;
  duration: number;
  price: number;
  is_connection: boolean;
  // connection-only:
  stop?: string;
  stop_arrival?: string;
  stop_departure?: string;
  stop_layover?: number;
  origin_city?: string;
  stop_city?: string;
  dest_city?: string;
}

export interface FourCitySolution {
  route: string[];
  bookings: FourCityBooking[];
  gaps: number[];
  total_price: number;
  departure_time: string;
  arrival_time: string;
  relaxed: boolean;
}

export interface FourCityRoutesResponse {
  travel_date: string | null;
  solutions: FourCitySolution[];
  refreshed_at: string | null;
}
