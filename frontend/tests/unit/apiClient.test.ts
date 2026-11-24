import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest, UNAUTHORIZED_EVENT } from "@/lib/apiClient";
import { ApiError, NetworkError } from "@/lib/errors";

function mockFetch(status: number, body: unknown) {
  const fn = vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("apiRequest", () => {
  it("unwraps data on success", async () => {
    mockFetch(200, { data: { id: "1" } });
    await expect(apiRequest<{ id: string }>("/api/boards")).resolves.toEqual({ id: "1" });
  });

  it("sends JSON bodies and never an Authorization header in the browser", async () => {
    const fn = mockFetch(201, { data: {} });
    await apiRequest("/api/boards", { method: "POST", body: { name: "A" } });
    const [, init] = fn.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe('{"name":"A"}');
    expect((init.headers as Record<string, string>).Authorization).toBeUndefined();
  });

  it("throws ApiError with statusCode and message on non-2xx", async () => {
    mockFetch(409, { error: "Email in use" });
    await expect(apiRequest("/api/auth/register", { method: "POST", body: {} })).rejects.toMatchObject({
      statusCode: 409,
      message: "Email in use",
    });
  });

  it("throws NetworkError when fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(apiRequest("/api/boards")).rejects.toBeInstanceOf(NetworkError);
  });

  it("announces a 401 so AuthContext can sign out, except for login", async () => {
    const listener = vi.fn();
    window.addEventListener(UNAUTHORIZED_EVENT, listener);
    mockFetch(401, { error: "Authentication required." });
    await expect(apiRequest("/api/boards")).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledTimes(1);
    mockFetch(401, { error: "Invalid email or password." });
    await expect(apiRequest("/api/session/login", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(UNAUTHORIZED_EVENT, listener);
  });
});