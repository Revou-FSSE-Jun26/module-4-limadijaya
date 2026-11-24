"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import BaseBadge from "@/components/shared/BaseBadge";
import BaseButton from "@/components/shared/BaseButton";
import { useNotifications } from "@/hooks/useNotifications";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import type { NotificationItem } from "@/types/api";

/** Header bell with the unread count. Polls every 30 seconds through useNotifications (FRONT-016, FRONT-017). */
export default function NotificationBell() {
  const router = useRouter();
  const panelId = useId();
  const handleError = useErrorHandler();
  const { items, unreadCount, failed, markRead } = useNotifications(true);
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    function onPointerDown(event: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) setOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("mousedown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("mousedown", onPointerDown);
    };
  }, [open]);

  async function openItem(item: NotificationItem) {
    try {
      if (!item.is_read) await markRead(item.id);
    } catch (error) {
      handleError(error);
    }
    setOpen(false);
    router.push(`/boards/${item.board_id}?card=${item.card_id}`);
  }

  return (
    <div ref={rootRef} className="relative">
      <BaseButton
        variant="secondary"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls={panelId}
        aria-label={`Notifications, ${unreadCount} unread`}
      >
        <span aria-hidden="true">🔔</span>
        <span data-testid="unread-count">
          {unreadCount > 0 ? <BaseBadge color="red">{unreadCount}</BaseBadge> : <span className="sr-only">0</span>}
        </span>
      </BaseButton>
      {open ? (
        <div id={panelId} className="absolute right-0 z-40 mt-2 w-72 max-w-[90vw] rounded-lg border border-slate-200 bg-white p-2 shadow-lg sm:w-80">
          {failed ? (
            <p role="status" className="px-2 py-1 text-xs text-amber-800">
              Notifications could not be updated.
            </p>
          ) : null}
          {items.length === 0 ? (
            <p className="px-2 py-3 text-sm text-slate-600">No notifications yet.</p>
          ) : (
            <ul className="max-h-80 space-y-1 overflow-y-auto">
              {items.map((item) => (
                <li key={item.id}>
                  <BaseButton variant="secondary" fullWidth onClick={() => void openItem(item)}>
                    <span className="flex w-full items-start gap-2 text-left">
                      {item.is_read ? null : <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red-600" aria-label="Unread" />}
                      <span className="min-w-0 whitespace-normal break-words">{item.message}</span>
                    </span>
                  </BaseButton>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}