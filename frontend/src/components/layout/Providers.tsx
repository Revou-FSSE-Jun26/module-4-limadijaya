"use client";

import type { ReactNode } from "react";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/context/AuthContext";
import type { UserPublic } from "@/types/api";

export interface ProvidersProps {
  initialUser: UserPublic | null;
  initialExpiresAt: string | null;
  children: ReactNode;
}

/** Mounts AuthContext and the react-hot-toast container once for the whole app. */
export default function Providers({ initialUser, initialExpiresAt, children }: ProvidersProps) {
  return (
    <AuthProvider initialUser={initialUser} initialExpiresAt={initialExpiresAt}>
      {children}
      <Toaster position="bottom-right" />
    </AuthProvider>
  );
}