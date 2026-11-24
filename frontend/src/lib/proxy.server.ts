import "server-only";

export const MAX_BODY_BYTES = 1_048_576;
export const UPSTREAM_TIMEOUT_MS = 25_000;
export const UNAVAILABLE_MESSAGE = "The service is temporarily unavailable.";

const ID = "[0-9a-fA-F-]{36}";

/** The only Flask routes the browser may reach through the proxy (FE-05). Login is handled by its own route. */
const ALLOWED: { method: string; pattern: RegExp; public?: boolean }[] = [
  { method: "GET", pattern: /^health$/, public: true },
  { method: "POST", pattern: /^auth\/register$/, public: true },
  { method: "GET", pattern: /^users\/me$/ },
  { method: "PATCH", pattern: /^users\/me$/ },
  { method: "GET", pattern: /^boards$/ },
  { method: "POST", pattern: /^boards$/ },
  { method: "GET", pattern: new RegExp(`^boards/${ID}$`) },
  { method: "PATCH", pattern: new RegExp(`^boards/${ID}$`) },
  { method: "DELETE", pattern: new RegExp(`^boards/${ID}$`) },
  { method: "POST", pattern: new RegExp(`^boards/${ID}/members$`) },
  { method: "POST", pattern: new RegExp(`^boards/${ID}/columns$`) },
  { method: "PATCH", pattern: new RegExp(`^boards/${ID}/columns/reorder$`) },
  { method: "GET", pattern: new RegExp(`^boards/${ID}/analytics$`) },
  { method: "PATCH", pattern: new RegExp(`^columns/${ID}$`) },
  { method: "DELETE", pattern: new RegExp(`^columns/${ID}$`) },
  { method: "POST", pattern: new RegExp(`^columns/${ID}/cards$`) },
  { method: "GET", pattern: /^cards$/ },
  { method: "PATCH", pattern: new RegExp(`^cards/${ID}$`) },
  { method: "DELETE", pattern: new RegExp(`^cards/${ID}$`) },
  { method: "PATCH", pattern: new RegExp(`^cards/${ID}/position$`) },
  { method: "GET", pattern: new RegExp(`^cards/${ID}/comments$`) },
  { method: "POST", pattern: new RegExp(`^cards/${ID}/comments$`) },
  { method: "PATCH", pattern: new RegExp(`^comments/${ID}$`) },
  { method: "DELETE", pattern: new RegExp(`^comments/${ID}$`) },
  { method: "GET", pattern: /^notifications$/ },
  { method: "PATCH", pattern: new RegExp(`^notifications/${ID}/read$`) },
];

export const STATE_CHANGING = new Set(["POST", "PATCH", "DELETE"]);

export interface RouteMatch {
  allowed: boolean;
  isPublic: boolean;
}

/** Normalizes the catch-all segments and checks them against the allow-list. */
export function matchRoute(method: string, segments: string[]): RouteMatch {
  const joined = segments.join("/");
  if (segments.some((part) => part === "" || part === "." || part === ".." || part.includes("\\") || part.includes("%"))) {
    return { allowed: false, isPublic: false };
  }
  const entry = ALLOWED.find((rule) => rule.method === method && rule.pattern.test(joined));
  return { allowed: Boolean(entry), isPublic: Boolean(entry?.public) };
}

/** Exact-match check against the explicitly trusted origins (DA-04). No wildcards, no suffix matching. */
export function trustedOrigins(env: string | undefined = process.env.APP_ORIGIN): string[] {
  const configured = (env ?? "")
    .split(",")
    .map((value) => value.trim().replace(/\/$/, ""))
    .filter(Boolean);
  if (configured.length === 0 && process.env.NODE_ENV !== "production") return ["http://localhost:3000"];
  return configured;
}

export function isTrustedOrigin(origin: string | null, trusted: string[] = trustedOrigins()): boolean {
  if (!origin || origin === "null") return false;
  return trusted.includes(origin);
}

export function jsonError(message: string, status: number, extraHeaders?: HeadersInit): Response {
  return Response.json({ error: message }, { status, headers: extraHeaders });
}

/** Reads the request body, enforcing the 1 MiB limit on both the header and the bytes actually read. */
export async function readLimitedBody(request: Request): Promise<string | "too-large"> {
  const declared = Number(request.headers.get("content-length") ?? "0");
  if (declared > MAX_BODY_BYTES) return "too-large";
  const buffer = await request.arrayBuffer();
  if (buffer.byteLength > MAX_BODY_BYTES) return "too-large";
  return new TextDecoder().decode(buffer);
}

export function upstreamUrl(path: string): string {
  const base = (process.env.API_BASE_URL ?? "").replace(/\/$/, "");
  return `${base}/api/${path}`;
}