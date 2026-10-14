"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut } from "lucide-react";

import { useAuth } from "./AuthProvider";

export function AccountMenu() {
  const { user, signOut } = useAuth();
  const router = useRouter();

  const [busy, setBusy] = useState(false);
  const [error, setError] =
    useState<string | null>(null);

  async function logout() {
    setBusy(true);
    setError(null);

    try {
      await signOut();
      router.replace("/login");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not log out. Please retry."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-2">
      <p
        className="truncate text-xs text-slate-500"
        title={user?.email}
      >
        {user?.email}
      </p>

      <button
        type="button"
        onClick={logout}
        disabled={busy}
        className="flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-brand-700 disabled:opacity-50"
      >
        <LogOut size={16} />
        {busy ? "Logging out…" : "Log out"}
      </button>

      {error && (
        <p
          role="alert"
          className="text-xs text-rose-600"
        >
          {error}
        </p>
      )}
    </div>
  );
}