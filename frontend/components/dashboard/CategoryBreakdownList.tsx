import type { CategoryBreakdownItem } from "@/types";
import { formatCurrency } from "@/lib/format";
import { capToOtherBucket, colorForIndex } from "@/lib/chartColors";

export function CategoryBreakdownList({ items }: { items: CategoryBreakdownItem[] }) {
  const capped = capToOtherBucket(items);
  const total = capped.reduce((sum, i) => sum + i.amount, 0);
  const data = capped.map((i) => ({ ...i, percent: total > 0 ? (i.amount / total) * 100 : 0 }));

  return (
    <ul className="space-y-3">
      {data.map((item, index) => (
        <li key={item.category}>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="flex items-center gap-2 text-slate-600">
              <span
                className="h-2.5 w-2.5 rounded-full shrink-0"
                style={{ backgroundColor: colorForIndex(index) }}
              />
              {item.category}
            </span>
            <span className="flex items-baseline gap-2">
              <span className="tabular-nums text-slate-400 text-xs">{formatCurrency(item.amount)}</span>
              <span className="tabular-nums text-slate-900 font-medium w-12 text-right">
                {item.percent.toFixed(1)}%
              </span>
            </span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{ width: `${item.percent}%`, backgroundColor: colorForIndex(index) }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}