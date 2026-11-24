/** Thrown by apiClient.ts for every non-2xx response (API-005). */
export class ApiError extends Error {
  readonly statusCode: number;

  constructor(statusCode: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

/** Thrown when no response arrives at all (offline, DNS, CORS, timeout). */
export class NetworkError extends Error {
  constructor(message = "The network request failed.") {
    super(message);
    this.name = "NetworkError";
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}
