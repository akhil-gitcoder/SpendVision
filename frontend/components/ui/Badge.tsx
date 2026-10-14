import { cn } from "@/lib/utils";

const CATEGORY_COLORS: Record<string, string> = {
  Food: "bg-orange-50 text-orange-700",
  Groceries: "bg-lime-50 text-lime-700",
  Transport: "bg-sky-50 text-sky-700",
  Shopping: "bg-fuchsia-50 text-fuchsia-700",
  Entertainment: "bg-violet-50 text-violet-700",
  Utilities: "bg-cyan-50 text-cyan-700",
  Healthcare: "bg-rose-50 text-rose-700",
  Education: "bg-indigo-50 text-indigo-700",
  Rent: "bg-amber-50 text-amber-700",
  Salary: "bg-emerald-50 text-emerald-700",
  Investment: "bg-teal-50 text-teal-700",
  Other: "bg-slate-100 text-slate-600",
  "Other Income": "bg-emerald-50 text-emerald-700",
  Uncategorized: "bg-slate-100 text-slate-500",
};

export function CategoryBadge({ category }: { category: string | null | undefined }) {
  const name = category || "Uncategorized";
  const color = CATEGORY_COLORS[name] || "bg-slate-100 text-slate-600";
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", color)}>
      {name}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: "info" | "positive" | "warning" }) {
  const styles = {
    info: "bg-slate-100 text-slate-600",
    positive: "bg-emerald-50 text-emerald-700",
    warning: "bg-amber-50 text-amber-700",
  }[severity];
  const label = { info: "Info", positive: "Positive", warning: "Notable" }[severity];
  return <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", styles)}>{label}</span>;
}
