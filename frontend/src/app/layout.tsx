import type { Metadata } from "next";
import type { ReactNode } from "react";
import { redirect } from "next/navigation";
import Providers from "@/components/layout/Providers";
import { apiRequest } from "@/lib/apiClient";
import { ApiError } from "@/lib/errors";
import { getSession } from "@/lib/session.server";
import type { UserPublic } from "@/types/api";
import "./globals.css";

export const metadata: Metadata = {
  title: "RevoTask",
  description: "RevoTask is a Trello-like task management application.",
};

export interface RootLayoutProps {
  children: ReactNode;
}

/** Loads the signed-in user on the server and hands plain JSON to the client Providers (FRONT-018-AC03). */
export default async function RootLayout({ children }: RootLayoutProps) {
  const session = await getSession();
  let user: UserPublic | null = null;
  if (session) {
    try {
      user = await apiRequest<UserPublic>("/api/users/me", { token: session.token });
    } catch (error) {
      if (error instanceof ApiError && error.statusCode === 401) redirect("/api/session/expire");
      // Other failures: render the page without a user. Protected pages show their own error.
    }
  }
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <Providers initialUser={user} initialExpiresAt={user && session ? session.expiresAt : null}>
          {children}
        </Providers>
      </body>
    </html>
  );
}