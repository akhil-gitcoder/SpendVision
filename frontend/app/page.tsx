"use client";

import { useState } from "react";
import { Wallet, TrendingDown, PiggyBank, Percent } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { StatCard } from "@/components/ui/StatCard";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { SpendingTrendChart } from "@/components/dashboard/SpendingTrendChart";
import { CategoryBreakdownList } from "@/components/dashboard/CategoryBreakdownList";
import { MonthComparisonList } from "@/components/dashboard/MonthComparisonList";
import { TransactionTable } from "@/components/transactions/TransactionTable";
import { useAsync } from "@/hooks/useAsync";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { cn } from "@/lib/utils";
import Link from "next/link";

const GRANULARITIES = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
] as const;

export default function DashboardPage() {
  const [granularity, setGranularity] = useState<"daily" | "weekly" | "monthly">("monthly");

  const summary = useAsync(() => api.getSummary(), []);
  const trend = useAsync(() => api.getMonthlyTrend(granularity), [granularity]);
  const breakdown = useAsync(() => api.getCategoryBreakdown(), []);
  const comparison = useAsync(() => api.getMonthComparison(), []);
  const recent = useAsync(() => api.listTransactions({ page: 1, page_size: 8 }), []);
  const topExpenses = useAsync(() => api.getTopExpenses(undefined, 5), []);

  const noDataYet =
    !summary.loading && !summary.error && summary.data && summary.data.transaction_count === 0;

  return (
    <div>
      <PageHeader title="Dashboard" description="Your financial overview at a glance." />

      <div className="p-4 md:p-8 space-y-6">
        {noDataYet ? (
          <Card>
            <EmptyState
              title="No transactions yet"
              description="Upload a CSV of your transactions to see your dashboard come to life."
              action={
                <Link
                  href="/upload"
                  className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
                >
                  Upload transactions
                </Link>
              }
            />
          </Card>
        ) : (
          <>
            {/* Summary cards */}
            {summary.loading ? (
              <LoadingState label="Loading summary…" />
            ) : summary.error ? (
              <ErrorState message={summary.error} onRetry={summary.refetch} />
            ) : summary.data ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Income" value={formatCurrency(summary.data.total_income)} icon={Wallet} tone="default" />
                <StatCard
                  label="Expenses"
                  value={formatCurrency(summary.data.total_expenses)}
                  icon={TrendingDown}
                  tone="warning"
                />
                <StatCard
                  label="Savings"
                  value={formatCurrency(summary.data.total_savings)}
                  icon={PiggyBank}
                  tone={summary.data.total_savings >= 0 ? "positive" : "danger"}
                />
                <StatCard
                  label="Savings Rate"
                  value={`${summary.data.savings_rate.toFixed(1)}%`}
                  icon={Percent}
                  tone={summary.data.savings_rate >= 20 ? "positive" : "default"}
                />
              </div>
            ) : null}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Spending trend */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Spending Trend</CardTitle>
                  <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
                    {GRANULARITIES.map((g) => (
                      <button
                        key={g.value}
                        onClick={() => setGranularity(g.value)}
                        className={cn(
                          "rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
                          granularity === g.value ? "bg-white text-slate-900 shadow-sm" : "text-slate-500"
                        )}
                      >
                        {g.label}
                      </button>
                    ))}
                  </div>
                </CardHeader>
                {trend.loading ? (
                  <LoadingState />
                ) : trend.error ? (
                  <ErrorState message={trend.error} onRetry={trend.refetch} />
                ) : trend.data && trend.data.points.length > 0 ? (
                  <SpendingTrendChart points={trend.data.points} />
                ) : (
                  <EmptyState title="No trend data" description="Upload transactions to see spending over time." />
                )}
              </Card>

              {/* Category breakdown */}
              <Card>
                <CardHeader>
                  <CardTitle>Category Breakdown</CardTitle>
                </CardHeader>
                {breakdown.loading ? (
                  <LoadingState />
                ) : breakdown.error ? (
                  <ErrorState message={breakdown.error} onRetry={breakdown.refetch} />
                ) : breakdown.data && breakdown.data.items.length > 0 ? (
                  <CategoryBreakdownList items={breakdown.data.items} />
                ) : (
                  <EmptyState title="No expenses this month" />
                )}
              </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Monthly comparison */}
              <Card>
                <CardHeader>
                  <CardTitle>Monthly Comparison</CardTitle>
                </CardHeader>
                {comparison.loading ? (
                  <LoadingState />
                ) : comparison.error ? (
                  <ErrorState message={comparison.error} onRetry={comparison.refetch} />
                ) : comparison.data ? (
                  <MonthComparisonList items={comparison.data.category_changes} />
                ) : null}
              </Card>

              {/* Top expenses */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Expenses</CardTitle>
                </CardHeader>
                {topExpenses.loading ? (
                  <LoadingState />
                ) : topExpenses.error ? (
                  <ErrorState message={topExpenses.error} onRetry={topExpenses.refetch} />
                ) : topExpenses.data && topExpenses.data.items.length > 0 ? (
                  <ul className="space-y-3">
                    {topExpenses.data.items.map((item) => (
                      <li key={item.id} className="flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium text-slate-800">{item.merchant || item.description}</p>
                          <p className="text-xs text-slate-400">{item.category}</p>
                        </div>
                        <span className="font-semibold tabular-nums text-slate-900">
                          {formatCurrency(item.amount)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <EmptyState title="No expenses yet" />
                )}
              </Card>

              {/* Recent transactions */}
              <Card className="lg:col-span-1">
                <CardHeader>
                  <CardTitle>Recent Transactions</CardTitle>
                  <Link href="/transactions" className="text-xs font-medium text-brand-600 hover:underline">
                    View all
                  </Link>
                </CardHeader>
                {recent.loading ? (
                  <LoadingState />
                ) : recent.error ? (
                  <ErrorState message={recent.error} onRetry={recent.refetch} />
                ) : recent.data && recent.data.items.length > 0 ? (
                  <ul className="space-y-3">
                    {recent.data.items.map((t) => (
                      <li key={t.id} className="flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium text-slate-800">{t.merchant || t.description}</p>
                          <p className="text-xs text-slate-400">{t.category?.name || "Uncategorized"}</p>
                        </div>
                        <span
                          className={cn(
                            "font-semibold tabular-nums",
                            t.transaction_type === "income" ? "text-emerald-600" : "text-slate-900"
                          )}
                        >
                          {t.transaction_type === "income" ? "+" : "-"}
                          {formatCurrency(t.amount)}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <EmptyState title="No transactions yet" />
                )}
              </Card>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
