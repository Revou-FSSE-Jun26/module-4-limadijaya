import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/session.server";
import { isTrustedOrigin, jsonError, readLimitedBody } from "@/lib/proxy.server";

export async function POST(request: Request) {
  if (!isTrustedOrigin(request.headers.get("origin"))) return jsonError("Request origin is not allowed.", 403);
  const body = await readLimitedBody(request);
  if (body === "too-large") return jsonError("Request body is too large.", 413);
  const response = NextResponse.json({ data: { ok: true } });
  response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true });
  return response;
}