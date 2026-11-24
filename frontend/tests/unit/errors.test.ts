import { describe, expect, it } from "vitest";
import { messageForError } from "@/hooks/useErrorHandler";
import { ApiError, NetworkError } from "@/lib/errors";

describe("ApiError", () => {
  it("carries statusCode and message", () => {
    const error = new ApiError(409, "Email in use");
    expect(error.statusCode).toBe(409);
    expect(error.message).toBe("Email in use");
    expect(error).toBeInstanceOf(Error);
  });
});

describe("messageForError", () => {
  it("shows the server text for 400 and 409", () => {
    expect(messageForError(new ApiError(400, "Invalid request: name."))).toBe("Invalid request: name.");
    expect(messageForError(new ApiError(409, "Already a member."))).toBe("Already a member.");
  });
  it("maps 401, 403, 404, and 5xx to fixed messages", () => {
    expect(messageForError(new ApiError(401, "x"))).toMatch(/session has expired/i);
    expect(messageForError(new ApiError(403, "x"))).toMatch(/permission/i);
    expect(messageForError(new ApiError(404, "x"))).toMatch(/could not be found/i);
    expect(messageForError(new ApiError(500, "stack trace"))).not.toContain("stack trace");
    expect(messageForError(new ApiError(504, "x"))).toMatch(/temporarily unavailable/i);
  });
  it("handles network and unknown errors", () => {
    expect(messageForError(new NetworkError())).toMatch(/network/i);
    expect(messageForError("boom")).toMatch(/something went wrong/i);
  });
});