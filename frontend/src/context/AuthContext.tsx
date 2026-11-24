"use client";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export interface AuthUser { id: string; name: string; email: string }
interface AuthContextValue { token: string | null; user: AuthUser | null; setSession: (token: string, user: AuthUser) => void; logout: () => void }
const emptyContext: AuthContextValue = { token: null, user: null, setSession: () => undefined, logout: () => undefined };
const AuthContext = createContext<AuthContextValue>(emptyContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null); const [user, setUser] = useState<AuthUser | null>(null);
  useEffect(() => { const stored = localStorage.getItem("revotask-session"); if (stored) { const session = JSON.parse(stored) as { token: string; user: AuthUser }; queueMicrotask(() => { setToken(session.token); setUser(session.user); }); } }, []);
  const setSession = (nextToken: string, nextUser: AuthUser) => { setToken(nextToken); setUser(nextUser); localStorage.setItem("revotask-session", JSON.stringify({ token: nextToken, user: nextUser })); };
  const logout = () => { setToken(null); setUser(null); localStorage.removeItem("revotask-session"); };
  return <AuthContext.Provider value={{ token, user, setSession, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth() { return useContext(AuthContext); }
