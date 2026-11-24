import "server-only";

/** Reads the `exp` claim (seconds since epoch) without verifying the signature. Flask is the only verifier. */
export function readJwtExp(token: string): number | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    const payload = JSON.parse(Buffer.from(parts[1], "base64url").toString("utf8")) as { exp?: unknown };
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

export function isJwtExpired(token: string, nowSeconds = Math.floor(Date.now() / 1000)): boolean {
  const exp = readJwtExp(token);
  return exp === null || exp <= nowSeconds;
}