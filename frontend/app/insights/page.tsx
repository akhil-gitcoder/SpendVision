"use client";

import { Sparkles, ShieldAlert, BadgeInfo } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/States";
import { InsightCard } from "@/components/insights/InsightCard";
import { AnomalyCard } from "@/components/insights/AnomalyCard";
import { useAsync } from "@/hooks/useAsync";
import { api } from "@/lib/api";

export default function InsightsPage() {
  const insights = useAsync(() => api.getInsights(), []);
  const anomalies = useAsync(() => api.getAnomalies(), []);

  return (
    <div>
      <PageHeader
        title="AI Insights"
        description="AI-generated observations about your spending, backed by numbers the backend already calculated."
      />

      <div className="p-4 md:p-8 space-y-6 max-w-4xl">
        <Card>
          <CardHeader>
            <CardTitle>
              <span className="flex items-center gap-2">
                <Sparkles size={16} className="text-brand-500" />
                Spending Insights
              </span>
            </CardTitle>
            {insights.data && !insights.data.ai_available && (
              <span className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500">
                <BadgeInfo size={12} />
                Template mode (no AI key configured)
              </span>
            )}
          </CardHeader>

          {insights.loading ? (
            <LoadingState label="Analyzing your spending…" />
          ) : insights.error ? (
            <ErrorState message={insights.error} onRetry={insights.refetch} />
          ) : insights.data && insights.data.insights.length > 0 ? (
            <div className="space-y-3">
              {insights.data.insights.map((insight, idx) => (
                <InsightCard key={idx} insight={insight} />
              ))}
            </div>
          ) : (
            <EmptyState title="No insights yet" description="Upload some transactions to get started." />
          )}
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>
              <span className="flex items-center gap-2">
                <ShieldAlert size={16} className="text-rose-500" />
                Unusual Spending
              </span>
            </CardTitle>
          </CardHeader>

          {anomalies.loading ? (
            <LoadingState label="Scanning for unusual transactions…" />
          ) : anomalies.error ? (
            <ErrorState message={anomalies.error} onRetry={anomalies.refetch} />
          ) : anomalies.data && anomalies.data.anomalies.length > 0 ? (
            <div className="space-y-3">
              {anomalies.data.anomalies.map((a) => (
                <AnomalyCard key={a.transaction_id} anomaly={a} />
              ))}
            </div>
          ) : (
            <EmptyState
              title="Nothing unusual detected"
              description="We'll flag transactions that are significantly larger than your typical spending in a category."
            />
          )}
        </Card>
      </div>
    </div>
  );
}
