import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchFlights, deleteFlight, toggleFlight } from '../api';
import FlightCard from '../components/FlightCard';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { data: flights, isLoading } = useQuery({
    queryKey: ['flights'],
    queryFn: fetchFlights,
    refetchInterval: 60000,
  });

  const deleteM = useMutation({
    mutationFn: deleteFlight,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flights'] }),
  });

  const toggleM = useMutation({
    mutationFn: toggleFlight,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['flights'] }),
  });

  if (isLoading) {
    return <p className="text-gray-400">Loading...</p>;
  }

  if (!flights || flights.length === 0) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400 text-lg mb-4">No flights tracked yet.</p>
        <Link
          to="/search"
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-3 rounded-lg transition-colors"
        >
          Search & Track Flights
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold">Tracked Flights</h1>
        <Link
          to="/search"
          className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Add Flight
        </Link>
      </div>
      {flights.map(f => (
        <FlightCard
          key={f.id}
          flight={f}
          onDelete={id => deleteM.mutate(id)}
          onToggle={id => toggleM.mutate(id)}
        />
      ))}
    </div>
  );
}
