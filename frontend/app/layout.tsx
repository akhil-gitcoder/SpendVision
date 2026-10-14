import type { Metadata } from "next";

import "./globals.css";

import { AuthProvider } from "@/components/auth/AuthProvider";
import { AppShell } from "@/components/auth/AppShell";

export const metadata: Metadata = {
  title: {
    default: "Dashboard",
    template: "%s",
  },
  description:
    "Upload transactions, track spending, and get AI-powered financial insights.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <AuthProvider>
          <AppShell>{children}</AppShell>
        </AuthProvider>
      </body>
    </html>
  );
}