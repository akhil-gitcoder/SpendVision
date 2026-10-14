"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  Eye,
  EyeOff,
  LockKeyhole,
  Wallet,
} from "lucide-react";

import { ApiError } from "@/lib/api";
import { useAuth } from "./AuthProvider";

export function AuthForm({
  mode,
}: {
  mode: "login" | "signup";
}) {
  const signup = mode === "signup";

  const { signIn, signUp } = useAuth();
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] =
    useState("");

  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] =
    useState<string | null>(null);

  async function submit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();
    setError(null);

    if (signup && password !== confirmation) {
      setError("Your passwords do not match.");
      return;
    }

    setBusy(true);

    try {
      if (signup) {
        await signUp(email.trim(), password);
      } else {
        await signIn(email.trim(), password);
      }

      setPassword("");
      setConfirmation("");

      router.replace("/");
    } catch (err) {
      if (
        err instanceof ApiError &&
        err.status === 422
      ) {
        setError(
          "Enter a valid email and password. New passwords need at least 8 characters."
        );
      } else {
        setError(
          err instanceof Error
            ? err.message
            : "Could not sign in. Please try again."
        );
      }
    } finally {
      setBusy(false);
    }
  }

  const fieldClass =
    "w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-100 disabled:opacity-60";

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <Link
          href="/login"
          className="mb-8 flex items-center justify-center gap-2 text-xl font-semibold text-slate-900"
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500 text-white">
            <Wallet size={22} />
          </span>

          SpendVision
        </Link>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-900">
            {signup
              ? "Create your account"
              : "Welcome back"}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            {signup
              ? "Start tracking your spending in your own private dashboard."
              : "Log in to see your transactions and spending insights."}
          </p>

          <form
            onSubmit={submit}
            className="mt-6 space-y-4"
          >
            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Email address
              </label>

              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                maxLength={255}
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                disabled={busy}
                className={fieldClass}
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Password
              </label>

              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={visible ? "text" : "password"}
                  autoComplete={
                    signup
                      ? "new-password"
                      : "current-password"
                  }
                  required
                  minLength={signup ? 8 : 1}
                  maxLength={128}
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  disabled={busy}
                  className={`${fieldClass} pr-11`}
                  aria-describedby={
                    signup
                      ? "password-help"
                      : undefined
                  }
                />

                <button
                  type="button"
                  onClick={() =>
                    setVisible((value) => !value)
                  }
                  aria-label={
                    visible
                      ? "Hide password"
                      : "Show password"
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {visible ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>

              {signup && (
                <p
                  id="password-help"
                  className="mt-1.5 text-xs text-slate-400"
                >
                  Use 8–128 characters. A longer
                  passphrase works well.
                </p>
              )}
            </div>

            {signup && (
              <div>
                <label
                  htmlFor="confirmation"
                  className="mb-1.5 block text-sm font-medium text-slate-700"
                >
                  Confirm password
                </label>

                <input
                  id="confirmation"
                  name="confirmation"
                  type={visible ? "text" : "password"}
                  autoComplete="new-password"
                  required
                  maxLength={128}
                  value={confirmation}
                  onChange={(event) =>
                    setConfirmation(event.target.value)
                  }
                  disabled={busy}
                  className={fieldClass}
                />
              </div>
            )}

            {error && (
              <p
                role="alert"
                className="rounded-lg bg-rose-50 p-3 text-sm text-rose-600"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={busy}
              className="w-full rounded-lg bg-brand-500 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-600 disabled:opacity-60"
            >
              {busy
                ? signup
                  ? "Creating account…"
                  : "Logging in…"
                : signup
                  ? "Create account"
                  : "Log in"}
            </button>
          </form>

          <p className="mt-5 text-center text-sm text-slate-500">
            {signup
              ? "Already have an account? "
              : "New to SpendVision? "}

            <Link
              href={signup ? "/login" : "/signup"}
              className="font-medium text-brand-600 hover:underline"
            >
              {signup ? "Log in" : "Create an account"}
            </Link>
          </p>
        </div>

        <p className="mt-6 flex items-center justify-center gap-1.5 text-xs text-slate-400">
          <LockKeyhole size={14} />
          Your transactions are visible only in your
          account.
        </p>
      </div>
    </div>
  );
}