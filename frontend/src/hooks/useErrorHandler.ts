"use client";
import { ApiError } from "@/lib/errors";
import { toast } from "@/lib/toast";
export function useErrorHandler() { return (error: unknown) => toast.error(error instanceof ApiError ? error.message : "Something went wrong."); }
