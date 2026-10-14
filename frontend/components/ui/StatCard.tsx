import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/Card";

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: "default" | "positive" | "warning" | "danger";
  sublabel?: string;
}

const TONE_STYLES: Record<string, string> = {
  default: "bg-brand-50 text-brand-600",
  positive: "bg-emerald-50 text-emerald-600",
  warning: "bg-amber-50 text-amber-600",
  danger: "bg-rose-50 text-rose-600",
};

export function StatCard({ label, value, icon: Icon, tone = "default", sublabel }: StatCardProps) {
  return (
    <Card className="flex items-start justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="mt-1.5 text-2xl font-semibold text-slate-900 tabular-nums">{value}</p>
        {sublabel && <p className="mt-1 text-xs text-slate-400">{sublabel}</p>}
      </div>
      <div className={cn("flex h-10 w-10 items-center justify-center rounded-lg", TONE_STYLES[tone])}>
        <Icon size={20} />
      </div>
    </Card>
  );
}
