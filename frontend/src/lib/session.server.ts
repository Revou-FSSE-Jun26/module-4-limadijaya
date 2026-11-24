import "server-only";
import { cookies } from "next/headers";
import { isJwtExpired, readJwtExp } from "@/lib/jwtExp.server";

export const SESSION_COOKIE = "revotask_session";

export interface SessionInfo {
  token: string;
  expiresAt: string;
}

/** The only module that reads the session cookie. The token never leaves the server (FE-04). */
export async function getSession(): Promise<SessionInfo | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token || isJwtExpired(token)) return null;
  const exp = readJwtExp(token);
  if (exp === null) return null;
  return { token, expiresAt: new Date(exp * 1000).toISOString() };
}

export function sessionCookieOptions(maxAgeSeconds: number) {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: Math.max(0, Math.floor(maxAgeSeconds)),
  };
}