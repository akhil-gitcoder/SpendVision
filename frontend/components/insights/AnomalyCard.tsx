import { AlertOctagon, CalendarDays } from "lucide-react";
import type { AnomalyItem } from "@/types";
import { formatCurrency, formatDate } from "@/lib/format";
import { CategoryBadge } from "@/components/ui/Badge";

export function AnomalyCard({ anomaly }: { anomaly: AnomalyItem }) {
  return (
    <div className="flex gap-3 rounded-xl border border-rose-100 bg-rose-50 p-4">
      <AlertOctagon size={18} className="mt-0.5 shrink-0 text-rose-500" />
      <div className="flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm font-semibold text-rose-700">
            <span>{anomaly.merchant || anomaly.description}</span>
            <span className="text-rose-300" aria-hidden="true">-</span>
            <span className="inline-flex items-center gap-1.5 font-semibold text-rose-800">
              <CalendarDays size={14} className="text-rose-500" aria-hidden="true" />
              <time dateTime={anomaly.transaction_date}>{formatDate(anomaly.transaction_date)}</time>
            </span>
          </p>
          <span className="font-semibold text-rose-700 tabular-nums">{formatCurrency(anomaly.amount)}</span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <CategoryBadge category={anomaly.category} />
        </div>
        <p className="mt-2 text-sm text-rose-700/90">{anomaly.reason}</p>
      </div>
    </div>
  );
}
