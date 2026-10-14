"use client";

import { useEffect } from "react";
import {
  usePathname,
  useRouter,
} from "next/navigation";

import { Sidebar } from "@/components/layout/Sidebar";
import { MobileNav } from "@/components/layout/MobileNav";

import { useAuth } from "./AuthProvider";
import { AccountMenu } from "./AccountMenu";

export function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const {
    user,
    loading,
    error,
    refresh,
  } = useAuth();

  const pathname = usePathname();
  const router = useRouter();

  const publicPage =
    pathname === "/login" ||
    pathname === "/signup";

  useEffect(() => {
    if (loading || error) return;

    if (!user && !publicPage) {
      router.replace("/login");
    } else if (user && publicPage) {
      router.replace("/");
    }
  }, [
    user,
    loading,
    error,
    publicPage,
    router,
  ]);

  if (loading) {
    return (
      <div
        role="status"
        className="min-h-screen flex items-center justify-center text-sm text-slate-500"
      >
        Checking your session…
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 p-6">
        <p
          role="alert"
          className="text-sm text-rose-600"
        >
          {error}
        </p>

        <button
          onClick={() => void refresh()}
          className="rounded-lg bg-brand-500 px-4 py-2 text-sm text-white"
        >
          Try again
        </button>
      </div>
    );
  }

  if (publicPage) {
    return user ? null : <main>{children}</main>;
  }

  if (!user) {
    return null;
  }

  return (
    <div key={user.id}>
      <Sidebar />

      <div className="md:pl-60">
        <div className="md:hidden border-b border-slate-200 bg-white px-4 py-3">
          <AccountMenu />
        </div>

        <main className="min-h-screen pb-20 md:pb-8">
          {children}
        </main>
      </div>

      <MobileNav />
    </div>
  );
}