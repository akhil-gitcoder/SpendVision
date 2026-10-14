import type { Transaction } from "@/types";
import { CategoryBadge } from "@/components/ui/Badge";
import { formatCurrency, formatDate } from "@/lib/format";
import { cn } from "@/lib/utils";

export function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
            <th className="py-2.5 pr-4 font-medium">Date</th>
            <th className="py-2.5 pr-4 font-medium">Merchant</th>
            <th className="py-2.5 pr-4 font-medium hidden md:table-cell">Description</th>
            <th className="py-2.5 pr-4 font-medium">Category</th>
            <th className="py-2.5 pl-4 font-medium text-right">Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60">
              <td className="py-3 pr-4 text-slate-500 whitespace-nowrap">{formatDate(t.transaction_date)}</td>
              <td className="py-3 pr-4 font-medium text-slate-800">{t.merchant || t.description}</td>
              <td className="py-3 pr-4 text-slate-500 hidden md:table-cell">{t.description}</td>
              <td className="py-3 pr-4">
                <CategoryBadge category={t.category?.name} />
              </td>
              <td
                className={cn(
                  "py-3 pl-4 text-right font-medium tabular-nums whitespace-nowrap",
                  t.transaction_type === "income" ? "text-emerald-600" : "text-slate-900"
                )}
              >
                {t.transaction_type === "income" ? "+" : "-"}
                {formatCurrency(t.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
