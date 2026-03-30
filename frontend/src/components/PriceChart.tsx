import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { PricePoint } from '../types';

interface Props {
  data: PricePoint[];
  baseline: number | null;
}

export default function PriceChart({ data, baseline }: Props) {
  if (data.length === 0) {
    return <p className="text-gray-400">No price history yet.</p>;
  }

  const chartData = data.map(d => ({
    time: new Date(d.checked_at + 'Z').toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    price: d.price,
  }));

  const prices = data.map(d => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = Math.max((maxPrice - minPrice) * 0.1, 5);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
        <XAxis dataKey="time" tick={{ fill: '#9ca3af', fontSize: 12 }} />
        <YAxis
          domain={[minPrice - padding, maxPrice + padding]}
          tick={{ fill: '#9ca3af', fontSize: 12 }}
          tickFormatter={v => `$${v}`}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: 8 }}
          labelStyle={{ color: '#9ca3af' }}
          formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
        />
        {baseline !== null && (
          <ReferenceLine
            y={baseline}
            stroke="#4ade80"
            strokeDasharray="5 5"
            label={{ value: `Baseline $${baseline}`, fill: '#4ade80', fontSize: 12 }}
          />
        )}
        <Line
          type="monotone"
          dataKey="price"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: '#3b82f6', r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
