import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { searchFlights, trackFlight } from '../api';
import SearchForm from '../components/SearchForm';
import SearchResults from '../components/SearchResults';
import type { FlightResult, SearchParams } from '../types';

export default function SearchPage() {
  const queryClient = useQueryClient();
  const [results, setResults] = useState<FlightResult[] | null>(null);
  const [lastSearch, setLastSearch] = useState<SearchParams | null>(null);
  const [trackingId, setTrackingId] = useState<string | null>(null);

  const searchM = useMutation({
    mutationFn: searchFlights,
    onSuccess: (data) => setResults(data),
  });

  const handleSearch = (params: SearchParams) => {
    setLastSearch(params);
    setResults(null);
    searchM.mutate(params);
  };

  const handleTrack = async (result: FlightResult) => {
    if (!lastSearch) return;
    const key = `${result.flight_codes}_${result.departure_time}`;
    setTrackingId(key);
    try {
      await trackFlight(result, lastSearch);
      queryClient.invalidateQueries({ queryKey: ['flights'] });
      setResults(prev => prev?.filter(r =>
        `${r.flight_codes}_${r.departure_time}` !== key
      ) ?? null);
    } finally {
      setTrackingId(null);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Search Flights</h1>
      <SearchForm onSearch={handleSearch} loading={searchM.isPending} />
      {searchM.error && (
        <p className="text-red-400 mt-4">Search failed: {String(searchM.error)}</p>
      )}
      {results && (
        <SearchResults results={results} onTrack={handleTrack} trackingId={trackingId} passengers={lastSearch?.adults ?? 1} />
      )}
    </div>
  );
}
