"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { CategoryChangeItem } from "@/types";
import { formatCurrency, formatPercent } from "@/lib/format";
import { STATUS_COLORS } from "@/lib/chartColors";

export function MonthComparisonList({ items }: { items: CategoryChangeItem[] }) {
  const visible = items.filter((i) => i.current_amount > 0 || i.previous_amount > 0).slice(0, 8);

  if (visible.length === 0) {
    return <p className="text-sm text-slate-500 py-6 text-center">Not enough data to compare months yet.</p>;
  }

  const maxAmount = Math.max(...visible.map((i) => Math.max(i.current_amount, i.previous_amount)), 1);

  return (
    <div className="space-y-4">
      {visible.map((item) => {
        const pct = item.change_percent;
        const increased = pct !== null && pct > 0;
        const decreased = pct !== null && pct < 0;
        const color = increased ? STATUS_COLORS.critical : decreased ? STATUS_COLORS.good : "#94a3b8";
        const Icon = increased ? ArrowUpRight : decreased ? ArrowDownRight : Minus;

        return (
          <div key={item.category}>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="font-medium text-slate-700">{item.category}</span>
              <span className="flex items-center gap-1 font-medium tabular-nums" style={{ color }}>
                <Icon size={14} />
                {formatPercent(pct)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${(item.current_amount / maxAmount) * 100}%`,
                    backgroundColor: color,
                  }}
                />
              </div>
              <span className="text-xs text-slate-400 tabular-nums w-24 text-right">
                {formatCurrency(item.current_amount)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
