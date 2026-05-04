import { useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchFourCityRoutes } from '../api';
import type { FourCityBooking, FourCitySolution } from '../types';

// Default MCTs (minutes), per city. Airport-level MCT is derived from the city.
const DEFAULT_MCT: Record<string, number> = {
  NYC: 180,
  ORD: 150,
  CHS: 90,
  AUS: 90,
  BNA: 90,
};

const MCT_CITIES = ['NYC', 'ORD', 'CHS', 'AUS', 'BNA'];

const CITY_LABELS: Record<string, string> = {
  NYC: 'New York City',
  ORD: 'Chicago',
  CHS: 'Charleston',
  AUS: 'Austin',
  BNA: 'Nashville',
};

const AIRLINE_LABELS: Record<string, string> = {
  UA: 'United',
  DL: 'Delta',
  AA: 'American',
  WN: 'Southwest',
  B6: 'JetBlue',
  AS: 'Alaska',
  F9: 'Frontier',
  NK: 'Spirit',
};

function carriersOf(b: FourCityBooking): string[] {
  return b.carriers && b.carriers.length > 0 ? b.carriers : [b.carrier];
}

function solutionCarriers(s: FourCitySolution): Set<string> {
  const set = new Set<string>();
  for (const b of s.bookings) for (const c of carriersOf(b)) set.add(c);
  return set;
}

const NYC_AIRPORTS = new Set(['LGA', 'JFK', 'EWR']);
const CHICAGO_AIRPORTS = new Set(['ORD', 'MDW']);

function cityFromAirport(code: string): string {
  if (NYC_AIRPORTS.has(code)) return 'NYC';
  if (CHICAGO_AIRPORTS.has(code)) return 'ORD';
  return code;
}

type SortMode =
  | 'cheapest'
  | 'expensive'
  | 'shortest'
  | 'longest'
  | 'earliest_NYC'
  | 'earliest_CHS'
  | 'earliest_BNA'
  | 'earliest_ORD'
  | 'earliest_AUS';

const SORT_OPTIONS: { value: SortMode; label: string }[] = [
  { value: 'cheapest', label: 'Cheapest → most expensive' },
  { value: 'expensive', label: 'Most expensive → cheapest' },
  { value: 'shortest', label: 'Shortest → longest duration' },
  { value: 'longest', label: 'Longest → shortest duration' },
  { value: 'earliest_NYC', label: 'Hit NYC earlier' },
  { value: 'earliest_CHS', label: 'Hit CHS earlier' },
  { value: 'earliest_BNA', label: 'Hit BNA earlier' },
  { value: 'earliest_ORD', label: 'Hit ORD earlier' },
  { value: 'earliest_AUS', label: 'Hit AUS earlier' },
];

function formatDuration(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatLayover(min: number): string {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function formatTimeOfDay(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
}

function totalDurationMinutes(s: FourCitySolution): number {
  return Math.round((new Date(s.arrival_time).getTime() - new Date(s.departure_time).getTime()) / 60000);
}

/** First arrival time at the target city, or null if it isn't visited. */
function earliestArrivalAtCity(s: FourCitySolution, city: string): number | null {
  for (const b of s.bookings) {
    if (b.is_connection && b.stop && cityFromAirport(b.stop) === city && b.stop_arrival) {
      return new Date(b.stop_arrival).getTime();
    }
    if (cityFromAirport(b.destination) === city) {
      return new Date(b.arrival).getTime();
    }
  }
  // Origin city counts at trip start (departure time).
  if (s.bookings.length > 0 && cityFromAirport(s.bookings[0].origin) === city) {
    return new Date(s.bookings[0].departure).getTime();
  }
  return null;
}

function isSolutionValid(s: FourCitySolution, mct: Record<string, number>): boolean {
  // gaps[i] is the gap after bookings[i]; the relevant city is bookings[i].destination's city
  for (let i = 0; i < s.gaps.length; i++) {
    const city = cityFromAirport(s.bookings[i].destination);
    const min = mct[city] ?? 60;
    if (s.gaps[i] < min) return false;
  }
  // Connection inner-layovers (stop_layover) must satisfy MCT at the stop city
  for (const b of s.bookings) {
    if (b.is_connection && b.stop && b.stop_layover != null) {
      const city = cityFromAirport(b.stop);
      const min = mct[city] ?? 60;
      if (b.stop_layover < min) return false;
    }
  }
  return true;
}

function timeAgo(iso: string | null): string {
  if (!iso) return 'never';
  const ms = Date.now() - new Date(iso).getTime();
  if (ms < 0) return 'just now';
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ${min % 60}m ago`;
  return new Date(iso).toLocaleString();
}

export default function FourCitiesPage() {
  const [mct, setMct] = useState<Record<string, number>>({ ...DEFAULT_MCT });
  const [sort, setSort] = useState<SortMode>('cheapest');
  const [airline, setAirline] = useState<string>('');  // '' means any
  const [numCities, setNumCities] = useState<3 | 4>(4);

  useEffect(() => {
    const prev = document.title;
    document.title = "Mother's Day Challenge Routes ✈️";
    return () => { document.title = prev; };
  }, []);

  const { data, isLoading, error } = useQuery({
    queryKey: ['four-city-routes'],
    queryFn: fetchFourCityRoutes,
    refetchInterval: 60_000, // re-fetch the cached payload every minute
  });

  const availableAirlines = useMemo(() => {
    const set = new Set<string>();
    for (const s of data?.solutions ?? []) {
      if (s.route.length !== numCities) continue;
      for (const c of solutionCarriers(s)) set.add(c);
    }
    return [...set].sort();
  }, [data, numCities]);

  const filteredSorted = useMemo(() => {
    if (!data?.solutions) return [];
    let filtered = data.solutions.filter((s) => s.route.length === numCities && isSolutionValid(s, mct));
    if (airline) {
      filtered = filtered.filter((s) => {
        const cs = solutionCarriers(s);
        return cs.size === 1 && cs.has(airline);
      });
    }

    const sorter: Record<SortMode, (a: FourCitySolution, b: FourCitySolution) => number> = {
      cheapest: (a, b) => a.total_price - b.total_price,
      expensive: (a, b) => b.total_price - a.total_price,
      shortest: (a, b) => totalDurationMinutes(a) - totalDurationMinutes(b),
      longest: (a, b) => totalDurationMinutes(b) - totalDurationMinutes(a),
      earliest_NYC: (a, b) => byEarliest(a, b, 'NYC'),
      earliest_CHS: (a, b) => byEarliest(a, b, 'CHS'),
      earliest_BNA: (a, b) => byEarliest(a, b, 'BNA'),
      earliest_ORD: (a, b) => byEarliest(a, b, 'ORD'),
      earliest_AUS: (a, b) => byEarliest(a, b, 'AUS'),
    };

    return [...filtered].sort(sorter[sort]);
  }, [data, mct, sort, airline, numCities]);

  const totalForCount = useMemo(() => {
    return (data?.solutions ?? []).filter((s) => s.route.length === numCities).length;
  }, [data, numCities]);

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1 flex-wrap gap-2 text-sm text-gray-400">
        <span>
          Charleston required + {numCities - 1} of {'{NYC, Nashville, Chicago, Austin}'}
          {data?.travel_date && <> · Travel date: <span className="text-gray-200">{data.travel_date}</span></>}
        </span>
        <span>
          Auto-refreshes every 30 min · Last refreshed:{' '}
          <span className="text-gray-200 font-medium" title={data?.refreshed_at ?? ''}>
            {timeAgo(data?.refreshed_at ?? null)}
          </span>
        </span>
      </div>
      <p className="text-xs text-gray-500 mb-6 italic">
        Filters out basic economy flights for flexibility's sake on challenge day
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        <aside className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Minimum Connection Times (min)</h2>
            <div className="space-y-1.5">
              {MCT_CITIES.map((city) => (
                <label key={city} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-gray-300 whitespace-nowrap">{CITY_LABELS[city] ?? city}</span>
                  <input
                    type="number"
                    min={0}
                    step={5}
                    value={mct[city]}
                    onChange={(e) =>
                      setMct((prev) => ({ ...prev, [city]: Number(e.target.value) || 0 }))
                    }
                    className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-right shrink-0"
                  />
                </label>
              ))}
            </div>
            <button
              className="mt-3 w-full text-xs bg-gray-700 hover:bg-gray-600 py-1.5 rounded"
              onClick={() => setMct({ ...DEFAULT_MCT })}
            >
              Reset to defaults
            </button>
          </div>

          <div className="bg-gray-800 rounded-lg p-4">
            <h2 className="text-sm font-semibold mb-3">Route length</h2>
            <div className="flex rounded-md overflow-hidden border border-gray-700">
              {([3, 4] as const).map((n) => (
                <button
                  key={n}
                  onClick={() => setNumCities(n)}
                  className={`flex-1 py-1.5 text-sm transition-colors ${
                    numCities === n
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {n} cities
                </button>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 space-y-3">
            <div>
              <label className="block text-sm font-semibold mb-2">Sort</label>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortMode)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-2 text-sm"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2">Airline</label>
              <select
                value={airline}
                onChange={(e) => setAirline(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-2 py-2 text-sm"
              >
                <option value="">Any airline</option>
                {availableAirlines.map((code) => (
                  <option key={code} value={code}>
                    {AIRLINE_LABELS[code] ?? code} only
                  </option>
                ))}
              </select>
            </div>
          </div>
        </aside>

        <main>
          {isLoading && <p className="text-gray-400">Loading…</p>}
          {error && <p className="text-red-400">Failed to load: {String(error)}</p>}
          {data && data.solutions.length === 0 && (
            <p className="text-gray-400">No solutions cached yet — wait for the next scheduled refresh.</p>
          )}
          {data && data.solutions.length > 0 && (
            <>
              <p className="text-sm text-gray-400 mb-4">
                {filteredSorted.length} of {totalForCount} {numCities}-city solutions match current filters
              </p>
              <div className="space-y-4">
                {filteredSorted.map((s, i) => (
                  <SolutionCard key={i} solution={s} index={i + 1} />
                ))}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function byEarliest(a: FourCitySolution, b: FourCitySolution, city: string): number {
  const ta = earliestArrivalAtCity(a, city);
  const tb = earliestArrivalAtCity(b, city);
  if (ta == null && tb == null) return 0;
  if (ta == null) return 1;
  if (tb == null) return -1;
  return ta - tb;
}

function SolutionCard({ solution, index }: { solution: FourCitySolution; index: number }) {
  const dur = totalDurationMinutes(solution);
  const route = solution.route.map((c) => CITY_LABELS[c] ?? c).join(' → ');
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <div className="font-semibold">
          <span className="text-gray-500 mr-2">{index}.</span>
          {route}
        </div>
        <div className="text-sm text-gray-400">
          ${solution.total_price.toFixed(2)} · {formatDuration(dur)}
        </div>
      </div>
      <div className="space-y-2">
        {solution.bookings.map((b, i) => (
          <BookingRow key={i} booking={b} gap={solution.gaps[i]} />
        ))}
      </div>
    </div>
  );
}

function BookingRow({ booking, gap }: { booking: FourCityBooking; gap: number | undefined }) {
  const dep = formatTimeOfDay(booking.departure);
  const arr = formatTimeOfDay(booking.arrival);
  const flightDur = Math.round(
    (new Date(booking.arrival).getTime() - new Date(booking.departure).getTime()) / 60000
  );

  return (
    <div className="text-sm">
      {booking.is_connection ? (
        <div>
          <span className="font-medium">
            {booking.origin} → {booking.stop} → {booking.destination}
          </span>{' '}
          <span className="text-gray-400">
            ({booking.carrier} {booking.flight_number})
          </span>{' '}
          | {dep} – {arr} ({formatDuration(flightDur)}) | ${booking.price.toFixed(2)}{' '}
          <span className="text-blue-400">
            ✈ Book as one flight with {formatLayover(booking.stop_layover ?? 0)} layover in {booking.stop}
          </span>
        </div>
      ) : (
        <div>
          <span className="font-medium">
            {booking.origin} → {booking.destination}
          </span>{' '}
          <span className="text-gray-400">
            ({booking.carrier} {booking.flight_number})
          </span>{' '}
          | {dep} – {arr} ({formatDuration(flightDur)}) | ${booking.price.toFixed(2)}
        </div>
      )}
      {gap != null && (
        <div className="text-xs text-gray-500 ml-4 mt-0.5">
          ⏱ Gap before next booking: {formatLayover(gap)} at {booking.destination}
        </div>
      )}
    </div>
  );
}
