// Продуктовая аналитика (PostHog, NFR-7). Имена событий — КОНТРАКТ с backend
// (см. backend/src/wizor/analytics/posthog.py::NorthStarEvent). Менять синхронно.

import posthog from "posthog-js";

export const NorthStarEvent = {
  PAGE_VIEWED: "page_viewed",
  AUDIT_STARTED: "audit_started",
  SCORE_CALCULATED: "score_calculated",
  FIX_APPLIED: "fix_applied",
} as const;

export type NorthStarEventName =
  (typeof NorthStarEvent)[keyof typeof NorthStarEvent];

/**
 * Инициализация PostHog. P1-решение (deferred self-host): без ключа — no-op,
 * капчур-вызовы безопасно игнорируются. Реальный инстанс включается на проде/P7.
 */
export function initAnalytics(apiKey: string | undefined, host: string): boolean {
  if (!apiKey || typeof window === "undefined") {
    return false;
  }
  posthog.init(apiKey, { api_host: host, capture_pageview: false });
  return true;
}

/** Зафиксировать событие. tenantId всегда кладётся в свойства (мульти-аренда). */
export function capture(
  event: NorthStarEventName,
  properties: Record<string, unknown> = {},
  tenantId?: string,
): void {
  const props = tenantId ? { ...properties, tenant_id: tenantId } : properties;
  if (typeof window === "undefined" || !posthog.__loaded) {
    return;
  }
  posthog.capture(event, props);
}
