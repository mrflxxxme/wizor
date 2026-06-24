import type { Metadata } from "next";

import { AnalyticsProvider } from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "WIZOR",
  description: "AI Readiness Platform для РФ",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <AnalyticsProvider>{children}</AnalyticsProvider>
      </body>
    </html>
  );
}
