import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { PricePoint } from "../types";
import { formatMoney } from "../api";

interface Props {
  points: PricePoint[];
}

export function PriceChart({ points }: Props) {
  if (points.length < 2) {
    return <p className="muted">Not enough price history to chart yet.</p>;
  }

  const data = points.map((p) => ({
    date: new Date(p.observed_at).toLocaleDateString(),
    price: Number(p.price_amount),
    currency: p.currency,
  }));

  return (
    <div className="chart-wrap">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e4dc" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => `$${Math.round(v / 1000)}k`}
          />
          <Tooltip formatter={(value: number) => formatMoney(String(value))} />
          <Line type="monotone" dataKey="price" stroke="#8b6914" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
