"use client";
import { BaseBadge } from "@/components/shared/BaseBadge";
import { useNotifications } from "@/hooks/useNotifications";
export function NotificationBell() { const { unreadCount } = useNotifications(); return <span aria-label="Notifications">🔔 {unreadCount > 0 && <BaseBadge>{String(unreadCount)}</BaseBadge>}</span>; }
