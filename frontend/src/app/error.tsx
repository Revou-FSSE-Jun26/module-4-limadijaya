"use client";

import BaseButton from "@/components/shared/BaseButton";

export interface ErrorPageProps {
  reset: () => void;
}

/** Last-resort boundary. Production builds hide server error text, so the message is generic. */
export default function ErrorPage({ reset }: ErrorPageProps) {
  return (
    <main className="mx-auto max-w-md p-8 text-center">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="mt-2 text-slate-600">Please try again.</p>
      <div className="mt-4">
        <BaseButton onClick={reset}>Try again</BaseButton>
      </div>
    </main>
  );
}