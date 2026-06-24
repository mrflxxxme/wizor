import { afterEach, describe, expect, it, vi } from "vitest";

import { capture, initAnalytics, NorthStarEvent } from "@/lib/analytics";
import { cn } from "@/lib/utils";

// Мокаем posthog-js: проверяем, что обёртка корректно вызывает SDK на truthy-ветках.
vi.mock("posthog-js", () => ({
  default: { init: vi.fn(), capture: vi.fn(), __loaded: true },
}));

import posthog from "posthog-js";

afterEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("NorthStarEvent contract", () => {
  it("matches backend event names (page_viewed/audit_started/...)", () => {
    expect(NorthStarEvent.PAGE_VIEWED).toBe("page_viewed");
    expect(NorthStarEvent.AUDIT_STARTED).toBe("audit_started");
    expect(NorthStarEvent.SCORE_CALCULATED).toBe("score_calculated");
    expect(NorthStarEvent.FIX_APPLIED).toBe("fix_applied");
  });
});

describe("initAnalytics", () => {
  it("is no-op without api key (P1 deferred self-host)", () => {
    expect(initAnalytics(undefined, "http://localhost:8000")).toBe(false);
    expect(initAnalytics("", "http://localhost:8000")).toBe(false);
  });

  it("initializes posthog when key + window present", () => {
    vi.stubGlobal("window", {});
    expect(initAnalytics("phc_test", "http://ph.local")).toBe(true);
    expect(posthog.init).toHaveBeenCalledWith("phc_test", {
      api_host: "http://ph.local",
      capture_pageview: false,
    });
  });
});

describe("capture", () => {
  it("does not throw when analytics is disabled (no window)", () => {
    expect(() =>
      capture(NorthStarEvent.AUDIT_STARTED, { source: "unit" }, "tenant-1"),
    ).not.toThrow();
  });

  it("forwards event + tenant_id to posthog when loaded", () => {
    vi.stubGlobal("window", {});
    capture(NorthStarEvent.SCORE_CALCULATED, { score: 42 }, "tenant-9");
    expect(posthog.capture).toHaveBeenCalledWith("score_calculated", {
      score: 42,
      tenant_id: "tenant-9",
    });
  });
});

describe("cn", () => {
  it("merges and dedupes tailwind classes", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-sm", false, "font-bold")).toBe("text-sm font-bold");
  });
});
