import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/session.server";
import {
  STATE_CHANGING,
  UNAVAILABLE_MESSAGE,
  UPSTREAM_TIMEOUT_MS,
  isTrustedOrigin,
  jsonError,
  matchRoute,
  readLimitedBody,
  upstreamUrl,
} from "@/lib/proxy.server";

interface RouteContext {
  params: Promise<{ path: string[] }>;
}

/** Same-origin proxy to Flask /api/*. It builds outgoing headers from scratch and checks the Origin (FE-05). */
async function handle(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const method = request.method.toUpperCase();
  const match = matchRoute(method, path);
  if (!match.allowed) return jsonError("Resource not found.", 404);

  if (STATE_CHANGING.has(method)) {
    if (!isTrustedOrigin(request.headers.get("origin"))) return jsonError("Request origin is not allowed.", 403);
    if (!(request.headers.get("content-type") ?? "").toLowerCase().startsWith("application/json")) {
      return jsonError("Content-Type must be application/json.", 415);
    }
  }

  const cookieHeader = request.headers.get("cookie") ?? "";
  const token = cookieHeader
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${SESSION_COOKIE}=`))
    ?.slice(SESSION_COOKIE.length + 1);
  if (!token && !match.isPublic) return jsonError("Authentication required.", 401);

  let body: string | undefined;
  if (STATE_CHANGING.has(method)) {
    const read = await readLimitedBody(request);
    if (read === "too-large") return jsonError("Request body is too large.", 413);
    body = read;
  }

  const search = new URL(request.url).search;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token && !match.isPublic) headers.Authorization = `Bearer ${decodeURIComponent(token)}`;

  try {
    const upstream = await fetch(`${upstreamUrl(path.join("/"))}${search}`, {
      method,
      headers,
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
    const text = await upstream.text();
    const response = new NextResponse(text, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
    });
    if (upstream.status === 401) response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true });
    return response;
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    return jsonError(UNAVAILABLE_MESSAGE, timedOut ? 504 : 502);
  }
}

export { handle as GET, handle as POST, handle as PATCH, handle as DELETE };