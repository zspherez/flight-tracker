import { Link } from 'react-router-dom';
import type { TrackedFlight } from '../types';

interface Props {
  flight: TrackedFlight;
  onDelete: (id: number) => void;
  onToggle: (id: number) => void;
}

export default function FlightCard({ flight, onDelete, onToggle }: Props) {
  const priceColor =
    flight.price_change === null || flight.price_change === 0
      ? 'text-gray-300'
      : flight.price_change < 0
        ? 'text-green-400'
        : 'text-red-400';

  const priceLabel =
    flight.price_change !== null && flight.price_change !== 0
      ? `${flight.price_change > 0 ? '+' : ''}$${flight.price_change.toFixed(2)} vs baseline`
      : flight.baseline_price !== null
        ? 'no change'
        : '';

  return (
    <div className={`bg-gray-800 rounded-xl p-5 ${!flight.is_active ? 'opacity-50' : ''}`}>
      <div className="flex items-start justify-between">
        <Link to={`/flights/${flight.id}`} className="flex-1 hover:opacity-80">
          <div className="flex items-center gap-3">
            <span className="font-mono font-bold text-lg">{flight.flight_codes}</span>
            <span className="text-gray-400">{flight.origin} {'->'} {flight.destination}</span>
          </div>
          <div className="flex items-center gap-4 mt-1 text-sm text-gray-400">
            <span>{flight.departure_time} - {flight.arrival_time}</span>
            <span>{flight.travel_date}</span>
            <span>{flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop`}</span>
          </div>
          <div className="mt-3 flex items-baseline gap-3">
            <span className={`text-2xl font-bold ${priceColor}`}>
              {flight.latest_price !== null ? `$${flight.latest_price.toFixed(0)}` : '--'}
            </span>
            {flight.adults > 1 && flight.latest_price !== null && (
              <span className="text-sm text-gray-400">${Math.round(flight.latest_price / flight.adults)}/person</span>
            )}
            {priceLabel && <span className={`text-sm ${priceColor}`}>{priceLabel}</span>}
            {flight.baseline_price !== null && (
              <span className="text-xs text-gray-500">baseline ${flight.baseline_price.toFixed(0)}</span>
            )}
          </div>
        </Link>
        <div className="flex gap-2 ml-4">
          <button
            onClick={() => onToggle(flight.id)}
            className="text-sm text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-gray-700"
          >
            {flight.is_active ? 'Pause' : 'Resume'}
          </button>
          <button
            onClick={() => onDelete(flight.id)}
            className="text-sm text-red-400 hover:text-red-300 px-2 py-1 rounded hover:bg-gray-700"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
