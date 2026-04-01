import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { TrackedFlight } from '../types';

interface Props {
  flight: TrackedFlight;
  onDelete: (id: number) => void;
  onToggle: (id: number) => void;
  onSetBaseline: (id: number, baseline: number | null) => void;
}

export default function FlightCard({ flight, onDelete, onToggle, onSetBaseline }: Props) {
  const [editing, setEditing] = useState(false);
  const [baselineInput, setBaselineInput] = useState(
    flight.baseline_price !== null ? String(flight.baseline_price) : ''
  );

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

  const pp = flight.adults > 1;

  const handleSaveBaseline = () => {
    const val = baselineInput.trim() ? Number(baselineInput) : null;
    onSetBaseline(flight.id, val);
    setEditing(false);
  };

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
            {pp && flight.latest_price !== null && (
              <span className="text-sm text-gray-400">${Math.round(flight.latest_price / flight.adults)}/pp</span>
            )}
            {priceLabel && <span className={`text-sm ${priceColor}`}>{priceLabel}</span>}
          </div>
        </Link>
        <div className="flex flex-col gap-2 ml-4 items-end">
          <div className="flex gap-2">
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
          {editing ? (
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={baselineInput}
                onChange={e => setBaselineInput(e.target.value)}
                placeholder="total price"
                className="w-24 bg-gray-700 rounded px-2 py-1 text-sm text-white outline-none"
                autoFocus
              />
              <button onClick={handleSaveBaseline} className="text-sm text-green-400 hover:text-green-300">Save</button>
              <button onClick={() => setEditing(false)} className="text-sm text-gray-400 hover:text-white">Cancel</button>
            </div>
          ) : (
            <button
              onClick={(e) => { e.preventDefault(); setEditing(true); }}
              className="text-xs text-gray-500 hover:text-gray-300"
            >
              baseline ${flight.baseline_price !== null ? flight.baseline_price.toFixed(0) : '--'}
              {pp && flight.baseline_price !== null && ` ($${Math.round(flight.baseline_price / flight.adults)}/pp)`}
              {' '}edit
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
