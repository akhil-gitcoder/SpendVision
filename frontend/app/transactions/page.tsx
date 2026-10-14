"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { useAsync } from "@/hooks/useAsync";
import { api } from "@/lib/api";

const CATEGORY_OPTIONS = [
  "Food",
  "Groceries",
  "Transport",
  "Shopping",
  "Entertainment",
  "Utilities",
  "Healthcare",
  "Education",
  "Rent",
  "Salary",
  "Investment",
  "Other",
  "Other Income",
];

const PAGE_SIZE = 20;

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [type, setType] = useState<"" | "income" | "expense">("");
  const [page, setPage] = useState(1);

  const { data, loading, error, refetch } = useAsync(
    () =>
      api.listTransactions({
        search: search || undefined,
        category: category || undefined,
        transaction_type: type || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    [search, category, type, page]
  );

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1;

  return (
    <div>
      <PageHeader title="Transactions" description="Browse and filter every transaction you've imported." />

      <div className="p-4 md:p-8 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
              placeholder="Search description…"
              className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
            />
          </div>

          <select
            value={category}
            onChange={(e) => {
              setPage(1);
              setCategory(e.target.value);
            }}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          >
            <option value="">All categories</option>
            {CATEGORY_OPTIONS.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            value={type}
            onChange={(e) => {
              setPage(1);
              setType(e.target.value as "" | "income" | "expense");
            }}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100"
          >
            <option value="">All types</option>
            <option value="income">Income</option>
            <option value="expense">Expense</option>
          </select>
        </div>

        <Card>
          {loading ? (
            <LoadingState label="Loading transactions…" />
          ) : error ? (
            <ErrorState message={error} onRetry={refetch} />
          ) : data && data.items.length > 0 ? (
            <>
              <TransactionTable transactions={data.items} />

              <div className="flex items-center justify-between pt-4 mt-4 border-t border-slate-100 text-sm">
                <p className="text-slate-500">
                  {data.total} transaction{data.total === 1 ? "" : "s"}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 disabled:opacity-40"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <span className="text-slate-500">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 disabled:opacity-40"
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <EmptyState
              title="No transactions found"
              description="Try adjusting your filters, or upload a CSV to get started."
            />
          )}
        </Card>
      </div>
    </div>
  );
}
