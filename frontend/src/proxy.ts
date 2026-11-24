import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE = "revotask_session";

/** Reads only the `exp` claim. The proxy never trusts the token, Flask verifies it. */
function isJwtExpired(token: string): boolean {
  const parts = token.split(".");
  if (parts.length !== 3) return true;
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, "+").replace(/_/g, "/"))) as { exp?: unknown };
    return typeof payload.exp !== "number" || payload.exp <= Math.floor(Date.now() / 1000);
  } catch {
    return true;
  }
}

/** Fast redirect for protected pages when the session cookie is missing or expired (FRONT-003). */
export function proxy(request: NextRequest) {
  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token || isJwtExpired(token)) {
    const response = NextResponse.redirect(new URL("/login", request.url));
    if (token) response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true });
    return response;
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/", "/boards/:path*", "/my-tasks", "/profile"],
};