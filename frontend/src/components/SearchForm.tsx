import { useState } from 'react';
import type { SearchParams } from '../types';

interface Props {
  onSearch: (params: SearchParams) => void;
  loading: boolean;
}

export default function SearchForm({ onSearch, loading }: Props) {
  const [origin, setOrigin] = useState('');
  const [destination, setDestination] = useState('');
  const [travelDate, setTravelDate] = useState('2026-05-10');
  const [maxStops, setMaxStops] = useState('ANY');
  const [adults, setAdults] = useState(1);
  const [airlines, setAirlines] = useState('');
  const [layoverAirports, setLayoverAirports] = useState('');
  const [departureFrom, setDepartureFrom] = useState('');
  const [departureTo, setDepartureTo] = useState('');
  const [excludeBasic, setExcludeBasic] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch({
      origin: origin.toUpperCase(),
      destination: destination.toUpperCase(),
      travel_date: travelDate,
      max_stops: maxStops,
      adults,
      airlines: airlines ? airlines.split(',').map(a => a.trim().toUpperCase()) : undefined,
      layover_airports: layoverAirports ? layoverAirports.split(',').map(a => a.trim().toUpperCase()) : undefined,
      departure_from: departureFrom ? Number(departureFrom) : undefined,
      departure_to: departureTo ? Number(departureTo) : undefined,
      exclude_basic_economy: excludeBasic,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-gray-800 rounded-xl p-6 space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Origin</label>
          <input
            value={origin}
            onChange={e => setOrigin(e.target.value)}
            placeholder="CHS"
            required
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Destination</label>
          <input
            value={destination}
            onChange={e => setDestination(e.target.value)}
            placeholder="EWR"
            required
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Date</label>
          <input
            type="date"
            value={travelDate}
            onChange={e => setTravelDate(e.target.value)}
            required
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Max Stops</label>
          <select
            value={maxStops}
            onChange={e => setMaxStops(e.target.value)}
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="ANY">Any</option>
            <option value="NON_STOP">Nonstop</option>
            <option value="ONE_STOP_OR_FEWER">1 stop or fewer</option>
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Passengers</label>
          <input
            type="number"
            min={1}
            max={9}
            value={adults}
            onChange={e => setAdults(Number(e.target.value))}
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Airlines (comma-separated)</label>
          <input
            value={airlines}
            onChange={e => setAirlines(e.target.value)}
            placeholder="UA, AA, DL"
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Layover airports</label>
          <input
            value={layoverAirports}
            onChange={e => setLayoverAirports(e.target.value)}
            placeholder="ORD, MDW"
            className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Departure window (hours)</label>
          <div className="flex gap-2">
            <input
              type="number"
              min={0}
              max={23}
              value={departureFrom}
              onChange={e => setDepartureFrom(e.target.value)}
              placeholder="6"
              className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
            />
            <span className="text-gray-400 self-center">-</span>
            <input
              type="number"
              min={0}
              max={23}
              value={departureTo}
              onChange={e => setDepartureTo(e.target.value)}
              placeholder="20"
              className="w-full bg-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>
        <div className="flex items-end">
          <label className="flex items-center gap-2 cursor-pointer pb-2">
            <input
              type="checkbox"
              checked={excludeBasic}
              onChange={e => setExcludeBasic(e.target.checked)}
              className="w-4 h-4 rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">Exclude basic economy</span>
          </label>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white font-medium px-6 py-2 rounded-lg transition-colors"
      >
        {loading ? 'Searching...' : 'Search Flights'}
      </button>
    </form>
  );
}
