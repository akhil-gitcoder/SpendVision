import { AlertTriangle, Info, Sparkles } from "lucide-react";
import type { InsightItem } from "@/types";
import { cn } from "@/lib/utils";

const SEVERITY_STYLES: Record<InsightItem["severity"], { icon: typeof Info; classes: string }> = {
  info: { icon: Info, classes: "bg-slate-50 text-slate-600 border-slate-200" },
  positive: { icon: Sparkles, classes: "bg-emerald-50 text-emerald-700 border-emerald-100" },
  warning: { icon: AlertTriangle, classes: "bg-amber-50 text-amber-700 border-amber-100" },
};

export function InsightCard({ insight }: { insight: InsightItem }) {
  const { icon: Icon, classes } = SEVERITY_STYLES[insight.severity];
  return (
    <div className={cn("flex gap-3 rounded-xl border p-4", classes)}>
      <Icon size={18} className="mt-0.5 shrink-0" />
      <div>
        <p className="text-sm font-semibold">{insight.title}</p>
        <p className="mt-1 text-sm opacity-90">{insight.detail}</p>
      </div>
    </div>
  );
}
