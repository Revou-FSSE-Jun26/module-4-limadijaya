import { describe, expect, it } from "vitest";
import { isTrustedOrigin, matchRoute } from "@/lib/proxy.server";

const ID = "123e4567-e89b-42d3-a456-426614174000";

describe("proxy allow-list", () => {
  it("allows the approved routes", () => {
    expect(matchRoute("GET", ["boards"]).allowed).toBe(true);
    expect(matchRoute("PATCH", ["cards", ID, "position"]).allowed).toBe(true);
    expect(matchRoute("GET", ["cards"]).allowed).toBe(true);
    expect(matchRoute("POST", ["auth", "register"])).toEqual({ allowed: true, isPublic: true });
  });
  it("never forwards login through the generic proxy", () => {
    expect(matchRoute("POST", ["auth", "login"]).allowed).toBe(false);
  });
  it("rejects wrong methods, unknown paths, and traversal", () => {
    expect(matchRoute("DELETE", ["boards"]).allowed).toBe(false);
    expect(matchRoute("GET", ["admin"]).allowed).toBe(false);
    expect(matchRoute("GET", ["boards", "..", "users", "me"]).allowed).toBe(false);
    expect(matchRoute("GET", ["boards", "%2e%2e"]).allowed).toBe(false);
    expect(matchRoute("GET", ["boards", "not-a-uuid"]).allowed).toBe(false);
  });
});

describe("trusted origins", () => {
  const trusted = ["https://revotask.example"];
  it("accepts only an exact match", () => {
    expect(isTrustedOrigin("https://revotask.example", trusted)).toBe(true);
    expect(isTrustedOrigin("https://revotask.example.evil.com", trusted)).toBe(false);
    expect(isTrustedOrigin("http://revotask.example", trusted)).toBe(false);
    expect(isTrustedOrigin("null", trusted)).toBe(false);
    expect(isTrustedOrigin(null, trusted)).toBe(false);
  });
});