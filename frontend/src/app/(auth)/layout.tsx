import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-8">
      <p className="mb-6 text-center text-3xl font-bold text-indigo-700">RevoTask</p>
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">{children}</div>
    </main>
  );
}