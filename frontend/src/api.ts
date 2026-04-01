import type { AirportOption, FlightResult, Notification, PricePoint, SearchParams, TrackedFlight } from './types';

const BASE = '';

export async function searchFlights(params: SearchParams): Promise<FlightResult[]> {
  const res = await fetch(`${BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchAirports(q: string): Promise<AirportOption[]> {
  if (!q) return [];
  const res = await fetch(`${BASE}/api/airports?q=${encodeURIComponent(q)}`);
  return res.json();
}

export async function fetchFlights(): Promise<TrackedFlight[]> {
  const res = await fetch(`${BASE}/api/flights`);
  return res.json();
}

export async function trackFlight(result: FlightResult, search: SearchParams): Promise<TrackedFlight> {
  const body = {
    origin: result.origin,
    destination: result.destination,
    travel_date: search.travel_date,
    flight_codes: result.flight_codes,
    departure_time: result.departure_time,
    arrival_time: result.arrival_time,
    stops: result.stops,
    duration: result.duration,
    adults: search.adults || 1,
    price: result.price,
    search_from_airports: [search.origin],
    search_to_airports: [search.destination],
    search_max_stops: search.max_stops,
    search_seat_type: search.seat_type || 'ECONOMY',
    search_airlines: search.airlines || null,
    search_layover_airports: search.layover_airports || null,
  };
  const res = await fetch(`${BASE}/api/flights`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteFlight(id: number): Promise<void> {
  await fetch(`${BASE}/api/flights/${id}`, { method: 'DELETE' });
}

export async function toggleFlight(id: number): Promise<TrackedFlight> {
  const res = await fetch(`${BASE}/api/flights/${id}`, { method: 'PATCH' });
  return res.json();
}

export async function fetchHistory(id: number): Promise<PricePoint[]> {
  const res = await fetch(`${BASE}/api/flights/${id}/history`);
  return res.json();
}

export async function fetchNotifications(): Promise<Notification[]> {
  const res = await fetch(`${BASE}/api/notifications`);
  return res.json();
}

export async function markNotificationRead(id: number): Promise<void> {
  await fetch(`${BASE}/api/notifications/${id}/read`, { method: 'PATCH' });
}

export async function setBaseline(id: number, baseline: number | null): Promise<TrackedFlight> {
  const res = await fetch(`${BASE}/api/flights/${id}/baseline`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ baseline }),
  });
  return res.json();
}
