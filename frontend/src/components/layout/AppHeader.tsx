"use client";

import Link from "next/link";
import NotificationBell from "@/components/notifications/NotificationBell";
import BaseButton from "@/components/shared/BaseButton";
import { useAuth } from "@/context/AuthContext";
import { useErrorHandler } from "@/hooks/useErrorHandler";
import { useState } from "react";

/** Header for every protected page: navigation, the notification bell, and logout (FRONT-004). */
export default function AppHeader() {
  const { currentUser, logout } = useAuth();
  const handleError = useErrorHandler();
  const [busy, setBusy] = useState(false);

  async function onLogout() {
    setBusy(true);
    try {
      await logout();
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <nav aria-label="Main" className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm font-medium">
          <Link href="/" className="text-lg font-bold text-indigo-700">
            RevoTask
          </Link>
          <Link href="/" className="min-h-11 content-center text-slate-700 hover:text-indigo-700">
            Boards
          </Link>
          <Link href="/my-tasks" className="min-h-11 content-center text-slate-700 hover:text-indigo-700">
            My Tasks
          </Link>
          <Link href="/profile" className="min-h-11 content-center text-slate-700 hover:text-indigo-700">
            Profile
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <span className="hidden text-sm text-slate-600 sm:inline">{currentUser?.name}</span>
          <NotificationBell />
          <BaseButton variant="secondary" loading={busy} onClick={onLogout}>
            Log out
          </BaseButton>
        </div>
      </div>
    </header>
  );
}