import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "RevoTask",
  description: "RevoTask is a Trello-like task management application.",
};

export interface RootLayoutProps {
  children: ReactNode;
}

// Placeholder root layout (T1.05). Session loading, AuthContext, and the toast
// container are added by later tasks (T10.07).
export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
