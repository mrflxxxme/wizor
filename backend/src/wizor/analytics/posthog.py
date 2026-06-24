"""Тонкая обёртка над PostHog (NFR-7) с безопасным no-op режимом.

P1-решение (deferred_live_gold): self-hosted PostHog-инстанс (ClickHouse-стек)
в dev-compose НЕ поднимается — он тяжёлый и не влезает в бюджет bootstrap.
Поэтому если ``posthog_api_key`` пуст, ``capture`` становится no-op: код всех
последующих фаз уже зовёт единый ``analytics.capture(...)``, а реальная отправка
включится переключением ключа на проде/P7. North Star события объявлены как
константы, чтобы имена не расходились между backend и frontend.
"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class NorthStarEvent(StrEnum):
    """Канонические имена North Star / активационных событий (NFR-7).

    Те же строки используются во frontend (lib/analytics). Менять — только
    синхронно с frontend, иначе воронка PostHog разъедется.
    """

    PAGE_VIEWED = "page_viewed"
    AUDIT_STARTED = "audit_started"
    SCORE_CALCULATED = "score_calculated"
    FIX_APPLIED = "fix_applied"


class AnalyticsClient:
    """Обёртка PostHog. Без ключа — no-op (см. модульный docstring)."""

    def __init__(self, api_key: str, host: str) -> None:
        self._enabled = bool(api_key)
        self._client: Any | None = None
        if self._enabled:
            # Импорт внутри ветки: пакет нужен только при реальной отправке.
            from posthog import Posthog

            self._client = Posthog(project_api_key=api_key, host=host)
        else:
            logger.info("posthog_disabled", reason="empty_api_key (P1 deferred)")

    def capture(
        self,
        event: NorthStarEvent | str,
        *,
        distinct_id: str | uuid.UUID,
        properties: dict[str, Any] | None = None,
        tenant_id: str | uuid.UUID | None = None,
    ) -> None:
        """Зафиксировать событие. tenant_id всегда кладётся в свойства (мульти-аренда)."""
        event_name = str(event)
        props = dict(properties or {})
        if tenant_id is not None:
            props["tenant_id"] = str(tenant_id)

        if not self._enabled or self._client is None:
            # ключ 'posthog_event' (не 'event') — 'event' зарезервирован structlog.
            logger.debug("analytics_noop", posthog_event=event_name, **props)
            return
        self._client.capture(distinct_id=str(distinct_id), event=event_name, properties=props)

    def shutdown(self) -> None:
        """Дослать буфер перед остановкой процесса."""
        if self._client is not None:
            self._client.shutdown()


def build_analytics_client(api_key: str, host: str) -> AnalyticsClient:
    """Фабрика клиента аналитики (вызывается в lifespan приложения)."""
    return AnalyticsClient(api_key=api_key, host=host)
