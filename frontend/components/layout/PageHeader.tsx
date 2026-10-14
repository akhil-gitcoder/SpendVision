export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur px-4 md:px-8 py-5">
      <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
      {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
    </div>
  );
}
