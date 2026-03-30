import type { FlightResult } from '../types';

interface Props {
  results: FlightResult[];
  onTrack: (result: FlightResult) => void;
  trackingId: string | null;
}

function formatDuration(min: number) {
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${h}h ${m}m`;
}

export default function SearchResults({ results, onTrack, trackingId }: Props) {
  if (results.length === 0) {
    return <p className="text-gray-400 mt-4">No flights found.</p>;
  }

  return (
    <div className="mt-6 space-y-3">
      {results.map(r => {
        const route = r.stops > 0
          ? r.legs.map(l => l.departure_airport).join(' \u2192 ') + ` \u2192 ${r.legs[r.legs.length - 1].arrival_airport}`
          : `${r.origin} \u2192 ${r.destination}`;
        const key = `${r.flight_codes}_${r.departure_time}`;

        return (
          <div key={key} className="bg-gray-800 rounded-lg p-4 flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <span className="font-mono font-bold text-white">{r.flight_codes}</span>
                <span className="text-gray-400 text-sm">{route}</span>
              </div>
              <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
                <span>{r.departure_time} - {r.arrival_time}</span>
                <span>{formatDuration(r.duration)}</span>
                <span>{r.stops === 0 ? 'Nonstop' : `${r.stops} stop`}</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xl font-bold text-green-400">${r.price}</span>
              <button
                onClick={() => onTrack(r)}
                disabled={trackingId === key}
                className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {trackingId === key ? 'Tracking...' : 'Track'}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
