import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchFlights, fetchHistory } from '../api';
import PriceChart from '../components/PriceChart';

function fmt(total: number, adults: number) {
  if (adults > 1) {
    return `$${total.toFixed(0)} ($${Math.round(total / adults)}/pp)`;
  }
  return `$${total.toFixed(0)}`;
}

export default function FlightDetailPage() {
  const { id } = useParams<{ id: string }>();
  const flightId = Number(id);

  const { data: flights } = useQuery({
    queryKey: ['flights'],
    queryFn: fetchFlights,
  });

  const { data: history, isLoading } = useQuery({
    queryKey: ['history', flightId],
    queryFn: () => fetchHistory(flightId),
    refetchInterval: 60000,
  });

  const flight = flights?.find(f => f.id === flightId);

  if (!flight) {
    return <p className="text-gray-400">Flight not found.</p>;
  }

  const a = flight.adults;
  const prices = history?.map(h => h.price) ?? [];
  const minPrice = prices.length ? Math.min(...prices) : null;
  const maxPrice = prices.length ? Math.max(...prices) : null;
  const avgPrice = prices.length ? prices.reduce((a, b) => a + b, 0) / prices.length : null;

  return (
    <div>
      <Link to="/" className="text-blue-400 hover:text-blue-300 text-sm mb-4 inline-block">
        &larr; Back to Dashboard
      </Link>

      <div className="bg-gray-800 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono font-bold text-xl">{flight.flight_codes}</span>
          <span className="text-gray-400">{flight.origin} {'->'} {flight.destination}</span>
          {a > 1 && <span className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">{a} passengers</span>}
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>{flight.departure_time} - {flight.arrival_time}</span>
          <span>{flight.travel_date}</span>
          <span>{flight.stops === 0 ? 'Nonstop' : `${flight.stops} stop`}</span>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 mb-1">Current</div>
            <div className="text-lg font-bold">
              {flight.latest_price !== null ? fmt(flight.latest_price, a) : '--'}
            </div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 mb-1">Baseline</div>
            <div className="text-lg font-bold text-green-400">
              {flight.baseline_price !== null ? fmt(flight.baseline_price, a) : '--'}
            </div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 mb-1">Min / Max</div>
            <div className="text-lg font-bold">
              {minPrice !== null ? `${fmt(minPrice, a)} / ${fmt(maxPrice!, a)}` : '--'}
            </div>
          </div>
          <div className="bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 mb-1">Average</div>
            <div className="text-lg font-bold">
              {avgPrice !== null ? fmt(avgPrice, a) : '--'}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-gray-800 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">Price History</h2>
        {isLoading ? (
          <p className="text-gray-400">Loading...</p>
        ) : (
          <PriceChart data={history ?? []} baseline={flight.baseline_price} />
        )}
      </div>
    </div>
  );
}
