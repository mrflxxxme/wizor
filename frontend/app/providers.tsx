"use client";

import { useEffect } from "react";

import { initAnalytics } from "@/lib/analytics";

// Провайдер аналитики. В P1 ключ обычно пуст → initAnalytics возвращает no-op
// (deferred self-host PostHog). Структура готова к включению на проде/P7.
export function AnalyticsProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initAnalytics(
      process.env.NEXT_PUBLIC_POSTHOG_KEY,
      process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "http://localhost:8000",
    );
  }, []);

  return <>{children}</>;
}
