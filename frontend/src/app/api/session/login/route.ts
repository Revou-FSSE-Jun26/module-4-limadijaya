import { NextResponse } from "next/server";
import { readJwtExp } from "@/lib/jwtExp.server";
import { SESSION_COOKIE, sessionCookieOptions } from "@/lib/session.server";
import {
  UNAVAILABLE_MESSAGE,
  UPSTREAM_TIMEOUT_MS,
  isTrustedOrigin,
  jsonError,
  readLimitedBody,
  upstreamUrl,
} from "@/lib/proxy.server";
import type { UserPublic } from "@/types/api";

/** The only route that calls Flask login. It stores the JWT in an HttpOnly cookie and never returns it. */
export async function POST(request: Request) {
  if (!isTrustedOrigin(request.headers.get("origin"))) return jsonError("Request origin is not allowed.", 403);
  if (!(request.headers.get("content-type") ?? "").toLowerCase().startsWith("application/json")) {
    return jsonError("Content-Type must be application/json.", 415);
  }
  const body = await readLimitedBody(request);
  if (body === "too-large") return jsonError("Request body is too large.", 413);

  try {
    const login = await fetch(upstreamUrl("auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
    const loginPayload = (await login.json().catch(() => null)) as
      | { data?: { access_token?: string }; error?: string }
      | null;
    const token = loginPayload?.data?.access_token;
    if (!login.ok || !token) {
      return jsonError(loginPayload?.error ?? "Login failed.", login.ok ? 502 : login.status);
    }

    const exp = readJwtExp(token);
    if (exp === null) return jsonError("Login failed.", 502);

    const me = await fetch(upstreamUrl("users/me"), {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
    const mePayload = (await me.json().catch(() => null)) as { data?: UserPublic } | null;
    if (!me.ok || !mePayload?.data) return jsonError("Login failed.", 502);

    const response = NextResponse.json({
      data: { user: mePayload.data, expires_at: new Date(exp * 1000).toISOString() },
    });
    response.cookies.set(SESSION_COOKIE, token, sessionCookieOptions(exp - Date.now() / 1000));
    return response;
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    return jsonError(UNAVAILABLE_MESSAGE, timedOut ? 504 : 502);
  }
}