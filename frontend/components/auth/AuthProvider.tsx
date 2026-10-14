"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { api, ApiError, type AuthUser } from "@/lib/api";

const TAB_LOGIN_KEY = "spendvision:tab-login-user";

function readTabLogin() {
  try {
    return sessionStorage.getItem(TAB_LOGIN_KEY);
  } catch {
    return null;
  }
}

function clearTabLogin() {
  try {
    sessionStorage.removeItem(TAB_LOGIN_KEY);
  } catch {
    // Unavailable storage is treated as a locked tab.
  }
}

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);

  const refresh = useCallback(async () => {
    const current = ++generation.current;
    const expectedUserId = readTabLogin();

    setError(null);

    // This tab must complete its own login first.
    if (!expectedUserId) {
      setUser(null);
      setLoading(false);
      return;
    }

    setLoading(true);

    try {
      const account = await api.me();

      if (current !== generation.current) return;

      if (account.id !== expectedUserId) {
        // Another tab changed the browser's signed-in account.
        clearTabLogin();
        setUser(null);
      } else {
        setUser(account);
      }
    } catch (err) {
      if (current !== generation.current) return;

      setUser(null);

      if (err instanceof ApiError && err.status === 401) {
        clearTabLogin();
      } else {
        setError(
          err instanceof Error
            ? err.message
            : "Could not check your session."
        );
      }
    } finally {
      if (current === generation.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const initialCheck = window.setTimeout(() => {
      void refresh();
    }, 0);

    const expire = () => {
      ++generation.current;
      clearTabLogin();
      setUser(null);
      setError(null);
      setLoading(false);
    };

    const visible = () => {
      if (document.visibilityState === "visible") {
        void refresh();
      }
    };

    window.addEventListener("spendvision:session-expired", expire);
    window.addEventListener("spendvision:auth-changed", visible);
    document.addEventListener("visibilitychange", visible);

    const channel =
      typeof BroadcastChannel !== "undefined"
        ? new BroadcastChannel("spendvision-auth")
        : null;

    if (channel) {
      channel.onmessage = () => void refresh();
    }

    return () => {
      window.clearTimeout(initialCheck);
      window.removeEventListener(
        "spendvision:session-expired",
        expire
      );
      window.removeEventListener(
        "spendvision:auth-changed",
        visible
      );
      document.removeEventListener("visibilitychange", visible);
      channel?.close();
    };
  }, [refresh]);

  function announce() {
    if (typeof BroadcastChannel !== "undefined") {
      const channel = new BroadcastChannel("spendvision-auth");
      channel.postMessage("changed");
      channel.close();
    }
  }

  function completeLogin(account: AuthUser) {
    try {
      sessionStorage.setItem(TAB_LOGIN_KEY, account.id);
    } catch {
      throw new Error(
        "Allow browser site storage to log in to SpendVision."
      );
    }

    ++generation.current;
    setUser(account);
    setError(null);
    setLoading(false);
    announce();
  }

  const signIn = async (email: string, password: string) => {
    completeLogin(await api.login(email, password));
  };

  const signUp = async (email: string, password: string) => {
    completeLogin(await api.signup(email, password));
  };

  const signOut = async () => {
    await api.logout();

    ++generation.current;
    clearTabLogin();
    setUser(null);
    setError(null);
    setLoading(false);
    announce();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        error,
        refresh,
        signIn,
        signUp,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }

  return context;
}