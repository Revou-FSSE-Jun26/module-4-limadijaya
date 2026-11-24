"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/apiClient";
import type { NotificationItem, NotificationPage } from "@/types/api";

export const POLL_INTERVAL_MS = 30_000;

export interface UseNotificationsResult {
  items: NotificationItem[];
  unreadCount: number;
  failed: boolean;
  refresh: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
}

/** Polls GET /api/notifications on mount and every 30 seconds, never overlapping requests (FE-17). */
export function useNotifications(enabled: boolean): UseNotificationsResult {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [failed, setFailed] = useState(false);
  const inFlight = useRef(false);

  const refresh = useCallback(async () => {
    if (inFlight.current) return;
    inFlight.current = true;
    try {
      const page = await api.get<NotificationPage>("/api/notifications?page=1&per_page=20");
      setItems(page.items);
      setUnreadCount(page.unread_count);
      setFailed(false);
    } catch {
      setFailed(true);
    } finally {
      inFlight.current = false;
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    // Fetching on mount synchronizes with the server, which is what an effect is for.
    const first = setTimeout(() => void refresh(), 0);
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => {
      clearTimeout(first);
      clearInterval(timer);
    };
  }, [enabled, refresh]);

  const markRead = useCallback(async (id: string) => {
    const updated = await api.patch<NotificationItem>(`/api/notifications/${id}/read`);
    setItems((current) => current.map((item) => (item.id === id ? updated : item)));
    setUnreadCount((count) => {
      const wasUnread = items.find((item) => item.id === id)?.is_read === false;
      return wasUnread ? Math.max(0, count - 1) : count;
    });
  }, [items]);

  return { items, unreadCount, failed, refresh, markRead };
}