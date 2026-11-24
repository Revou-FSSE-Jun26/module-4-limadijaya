import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { POLL_INTERVAL_MS, useNotifications } from "@/hooks/useNotifications";

const api = vi.hoisted(() => ({ get: vi.fn(), patch: vi.fn() }));
vi.mock("@/lib/apiClient", () => ({ api }));

const page = (unread: number) => ({ items: [], page: 1, per_page: 20, total: unread, unread_count: unread });

describe("useNotifications", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    api.get.mockReset();
  });
  afterEach(() => vi.useRealTimers());

  it("polls on mount and every 30 seconds, and exposes the unread count", async () => {
    api.get.mockResolvedValue(page(2));
    const { result, unmount } = renderHook(() => useNotifications(true));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(result.current.unreadCount).toBe(2);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    expect(api.get).toHaveBeenCalledTimes(2);
    unmount();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 2);
    });
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it("makes no request while disabled and flags a failed poll", async () => {
    const disabled = renderHook(() => useNotifications(false));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    expect(api.get).not.toHaveBeenCalled();
    disabled.unmount();

    api.get.mockRejectedValue(new Error("down"));
    const { result } = renderHook(() => useNotifications(true));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(result.current.failed).toBe(true);
  });
});