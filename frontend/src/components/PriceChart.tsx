import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';
import type { PricePoint } from '../types';

interface Props {
  data: PricePoint[];
  baseline: number | null;
}

export default function PriceChart({ data, baseline }: Props) {
  if (data.length === 0) {
    return <p className="text-gray-400">No price history yet.</p>;
  }

  const chartData = data.map((d) => ({
    time: new Date(d.checked_at.replace(' ', 'T') + 'Z').toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    price: d.price,
  }));

  const prices = data.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const range = maxPrice - minPrice;
  // For flat data (single point or zero variance), give the chart breathing
  // room — otherwise recharts picks awkward fractional ticks.
  const padding = range > 0 ? range * 0.15 : Math.max(maxPrice * 0.02, 20);
  const latestPrice = chartData[chartData.length - 1]?.price;

  return (
    <div>
      <div className="flex items-center gap-5 text-xs mb-3">
        {latestPrice != null && (
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-2 h-2 rounded-full bg-blue-500" />
            <span className="text-gray-400">Current</span>
            <span className="text-gray-200 font-medium">${latestPrice.toFixed(2)}</span>
          </span>
        )}
        {baseline != null && (
          <span className="flex items-center gap-1.5">
            <svg width="14" height="2" className="shrink-0">
              <line
                x1="0"
                y1="1"
                x2="14"
                y2="1"
                stroke="#4ade80"
                strokeWidth="2"
                strokeDasharray="3 2"
              />
            </svg>
            <span className="text-gray-400">Baseline</span>
            <span className="text-green-400 font-medium">${baseline.toFixed(2)}</span>
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData} margin={{ top: 5, right: 16, bottom: 5, left: 0 }}>
          <defs>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis
            dataKey="time"
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickFormatter={(v) => `$${Math.round(v)}`}
            tickLine={false}
            axisLine={false}
            width={56}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: 8,
            }}
            labelStyle={{ color: '#9ca3af', marginBottom: 4 }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Price']}
          />
          {baseline != null && (
            <ReferenceLine
              y={baseline}
              stroke="#4ade80"
              strokeDasharray="4 4"
              strokeOpacity={0.6}
            />
          )}
          <Area
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#priceFill)"
            dot={{ fill: '#3b82f6', stroke: '#0f172a', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: '#0f172a', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
