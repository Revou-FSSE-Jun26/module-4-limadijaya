import "server-only";
import { notFound, redirect } from "next/navigation";
import { apiRequest } from "@/lib/apiClient";
import { ApiError } from "@/lib/errors";
import { getSession } from "@/lib/session.server";

/**
 * Authenticated GET for Server Components (FE-03).
 * 401 sends the user through /api/session/expire (a Server Component cannot clear cookies).
 * 404 renders the not-found page. Other errors are rethrown so the page can show ErrorState.
 */
export async function serverGet<T>(path: string): Promise<T> {
  const session = await getSession();
  if (!session) redirect("/api/session/expire");
  try {
    return await apiRequest<T>(path, { token: session.token });
  } catch (error) {
    if (error instanceof ApiError && error.statusCode === 401) redirect("/api/session/expire");
    if (error instanceof ApiError && error.statusCode === 404) notFound();
    throw error;
  }
}

/** Like serverGet, but returns the error instead of throwing, so a page can render an inline ErrorState. */
export async function serverGetResult<T>(path: string): Promise<{ data: T; error: null } | { data: null; error: string }> {
  try {
    return { data: await serverGet<T>(path), error: null };
  } catch (error) {
    if (error instanceof ApiError) return { data: null, error: error.message };
    if (error instanceof Error && "digest" in error) throw error; // redirect() and notFound() signals
    return { data: null, error: "The service is temporarily unavailable." };
  }
}