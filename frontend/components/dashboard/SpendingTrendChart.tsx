"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { MonthlyPoint } from "@/types";
import { formatCompactCurrency, formatCurrency } from "@/lib/format";
import { CATEGORICAL_COLORS, CHART_INK } from "@/lib/chartColors";

function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-md text-xs">
      <p className="font-medium text-slate-700 mb-1">{label}</p>
      {payload.map((entry: any) => (
        <p key={entry.dataKey} style={{ color: entry.color }} className="tabular-nums">
          {entry.name}: {formatCurrency(entry.value)}
        </p>
      ))}
    </div>
  );
}

type SeriesKey = "income" | "expenses";

function TrendSeriesChart({
  points,
  dataKey,
  label,
  color,
}: {
  points: MonthlyPoint[];
  dataKey: SeriesKey;
  label: string;
  color: string;
}) {
  const gradientId = `${dataKey}Fill`;
  return (
    <div>
      <div className="mb-1 flex items-center gap-2 text-xs font-medium" style={{ color }}>
        <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: color }} />
        {label}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart
          data={points}
          syncId="spending-trend"
          margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_INK.grid} vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 12, fill: CHART_INK.muted }}
            axisLine={{ stroke: CHART_INK.baseline }}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            tick={{ fontSize: 12, fill: CHART_INK.muted }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => formatCompactCurrency(v)}
            width={64}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey={dataKey}
            name={label}
            stroke={color}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SpendingTrendChart({ points }: { points: MonthlyPoint[] }) {
  return (
    <div className="space-y-6">
      <TrendSeriesChart
        points={points}
        dataKey="income"
        label="Income"
        color={CATEGORICAL_COLORS[0]}
      />
      <TrendSeriesChart
        points={points}
        dataKey="expenses"
        label="Expenses"
        color={CATEGORICAL_COLORS[1]}
      />
    </div>
  );
}
