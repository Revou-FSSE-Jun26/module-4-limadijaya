import { NextResponse } from "next/server";
import { SESSION_COOKIE } from "@/lib/session.server";

/** Server Components cannot set cookies, so they redirect here after Flask rejects the token. */
export async function GET(request: Request) {
  const response = NextResponse.redirect(new URL("/login", request.url));
  response.cookies.set(SESSION_COOKIE, "", { path: "/", maxAge: 0, httpOnly: true });
  return response;
}