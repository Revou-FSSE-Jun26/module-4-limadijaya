import { ApiError, NetworkError } from "@/lib/errors";

export type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export interface ApiRequestOptions {
  method?: HttpMethod;
  body?: unknown;
  /** Bearer token. Only the server-side wrapper passes it. Browser code never sees the JWT (FE-04). */
  token?: string | null;
  signal?: AbortSignal;
}

/** Event fired in the browser when a proxied call returns 401, so AuthContext can sign the user out. */
export const UNAUTHORIZED_EVENT = "revotask:unauthorized";

const isServer = typeof window === "undefined";

/**
 * Base URL by runtime (FE-06):
 * - Server Components use API_BASE_URL and talk to Flask directly with a Bearer token.
 * - Client Components use the same-origin Next.js proxy ("") so the HttpOnly session cookie
 *   authenticates the call and the token never reaches browser JavaScript.
 */
export function getBaseUrl(): string {
  if (isServer) {
    return (process.env.API_BASE_URL ?? "").replace(/\/$/, "");
  }
  return "";
}

function extractError(payload: unknown, status: number): string {
  if (payload && typeof payload === "object" && "error" in payload) {
    const message = (payload as { error: unknown }).error;
    if (typeof message === "string" && message.length > 0) return message;
  }
  return `Request failed with status ${status}.`;
}

/** Typed fetch wrapper: resolves with the `data` value, throws ApiError on non-2xx. */
export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, signal } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  let response: Response;
  try {
    response = await fetch(`${getBaseUrl()}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: "no-store",
      credentials: "same-origin",
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new NetworkError();
  }

  let payload: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    if (response.status === 401 && !isServer && !path.startsWith("/api/session/login")) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    throw new ApiError(response.status, extractError(payload, response.status));
  }
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

/** The one direct browser call to Flask: GET /api/health (design 7.5). */
export async function checkHealth(): Promise<{ status: string }> {
  const base = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "").replace(/\/$/, "");
  const response = await fetch(`${base}/api/health`, { cache: "no-store" });
  if (!response.ok) throw new ApiError(response.status, "The API is not healthy.");
  const payload = (await response.json()) as { data: { status: string } };
  return payload.data;
}

export const api = {
  get: <T>(path: string, signal?: AbortSignal) => apiRequest<T>(path, { signal }),
  post: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "POST", body: body ?? {} }),
  patch: <T>(path: string, body?: unknown) => apiRequest<T>(path, { method: "PATCH", body: body ?? {} }),
  delete: <T>(path: string) => apiRequest<T>(path, { method: "DELETE" }),
};
