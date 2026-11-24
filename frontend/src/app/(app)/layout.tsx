import type { ReactNode } from "react";
import AppHeader from "@/components/layout/AppHeader";

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <AppHeader />
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </>
  );
}