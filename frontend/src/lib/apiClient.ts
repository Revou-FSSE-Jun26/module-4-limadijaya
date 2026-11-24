import { ApiError } from "./errors";

const clientBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000/api";
const serverBase = process.env.API_BASE_URL ?? clientBase;

export async function apiClient<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${typeof window === "undefined" ? serverBase : clientBase}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, body.error ?? "Request failed.");
  return body.data as T;
}
