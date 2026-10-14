"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-500">
        <AlertTriangle size={22} />
      </div>
      <div>
        <p className="text-sm font-semibold text-slate-800">Something went wrong</p>
        <p className="mt-1 max-w-sm text-sm text-slate-500">
          An unexpected error occurred while loading this page. Please try again.
        </p>
      </div>
      <button
        onClick={reset}
        className="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-600"
      >
        Try again
      </button>
    </div>
  );
}
