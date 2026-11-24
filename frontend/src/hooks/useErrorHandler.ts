"use client";

import { useCallback } from "react";
import { ApiError, NetworkError } from "@/lib/errors";
import { toastError } from "@/lib/toast";

/** Maps an ApiError status code to the text shown in a toast (FE-07, API-006). */
export function messageForError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.statusCode) {
      case 400:
      case 409:
        return error.message;
      case 401:
        return "Your session has expired. Please log in again.";
      case 403:
        return "You do not have permission to do that.";
      case 404:
        return "That item could not be found. It may have been removed.";
      case 413:
        return "That request is too large.";
      case 502:
      case 504:
        return "The service is temporarily unavailable. Please try again.";
      default:
        return error.statusCode >= 500 ? "Something went wrong on our side. Please try again." : error.message;
    }
  }
  if (error instanceof NetworkError) return "Network error. Check your connection and try again.";
  return "Something went wrong. Please try again.";
}

export function useErrorHandler() {
  return useCallback((error: unknown, fallback?: string) => {
    const message = fallback && !(error instanceof ApiError) && !(error instanceof NetworkError) ? fallback : messageForError(error);
    toastError(message);
    return message;
  }, []);
}