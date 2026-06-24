"""Unit: PostHog-абстракция в no-op режиме (P1 deferred self-host)."""

from __future__ import annotations

import uuid

from wizor.analytics.posthog import (
    AnalyticsClient,
    NorthStarEvent,
    build_analytics_client,
)


def test_client_disabled_without_key() -> None:
    client = build_analytics_client(api_key="", host="http://localhost:8000")
    assert isinstance(client, AnalyticsClient)
    # capture в no-op режиме не должен бросать и не требует сети.
    client.capture(
        NorthStarEvent.AUDIT_STARTED,
        distinct_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        properties={"source": "unit"},
    )
    client.shutdown()


def test_northstar_event_values_stable() -> None:
    # Имена событий — контракт с frontend; фиксируем их строки.
    assert NorthStarEvent.PAGE_VIEWED == "page_viewed"
    assert NorthStarEvent.AUDIT_STARTED == "audit_started"
    assert NorthStarEvent.SCORE_CALCULATED == "score_calculated"
    assert NorthStarEvent.FIX_APPLIED == "fix_applied"
