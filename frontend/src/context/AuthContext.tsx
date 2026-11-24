"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { UNAUTHORIZED_EVENT, api, apiRequest } from "@/lib/apiClient";
import type { LoginResult, SessionState, UserPublic } from "@/types/api";

export interface AuthContextValue {
  currentUser: UserPublic | null;
  session: SessionState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (input: { name: string; email: string }) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export interface AuthProviderProps {
  initialUser: UserPublic | null;
  initialExpiresAt: string | null;
  children: ReactNode;
}

/** Holds the signed-in user. The JWT itself lives only in the HttpOnly cookie and is never in this value (FE-08). */
export function AuthProvider({ initialUser, initialExpiresAt, children }: AuthProviderProps) {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<UserPublic | null>(initialUser);
  const [session, setSession] = useState<SessionState>({
    authenticated: initialUser !== null,
    expiresAt: initialExpiresAt,
  });

  const clear = useCallback(() => {
    setCurrentUser(null);
    setSession({ authenticated: false, expiresAt: null });
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const result = await apiRequest<LoginResult>("/api/session/login", { method: "POST", body: { email, password } });
      setCurrentUser(result.user);
      setSession({ authenticated: true, expiresAt: result.expires_at });
      router.push("/");
      router.refresh();
    },
    [router],
  );

  const logout = useCallback(async () => {
    try {
      await api.post("/api/session/logout");
    } finally {
      clear();
      router.push("/login");
      router.refresh();
    }
  }, [clear, router]);

  const updateProfile = useCallback(async (input: { name: string; email: string }) => {
    const user = await api.patch<UserPublic>("/api/users/me", { name: input.name, email: input.email });
    setCurrentUser(user);
  }, []);

  // A proxied 401 means the session ended: sign out locally and go to /login (API-005-AC05).
  useEffect(() => {
    function onUnauthorized() {
      clear();
      router.push("/login");
    }
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [clear, router]);

  // The session expires at the JWT exp: clear the user at that moment.
  useEffect(() => {
    if (!session.expiresAt) return;
    const remaining = new Date(session.expiresAt).getTime() - Date.now();
    if (remaining <= 0) return;
    const timer = setTimeout(() => {
      clear();
      router.push("/login");
    }, Math.min(remaining, 2_147_000_000));
    return () => clearTimeout(timer);
  }, [session.expiresAt, clear, router]);

  const value = useMemo(
    () => ({ currentUser, session, login, logout, updateProfile }),
    [currentUser, session, login, logout, updateProfile],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider.");
  return value;
}