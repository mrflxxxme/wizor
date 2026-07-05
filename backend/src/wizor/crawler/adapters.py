"""Pluggable-адаптеры Core Web Vitals и индексируемости (форки #4/#5 PLAN).

CWV и индексируемость (Bing IndexNow / Яндекс.Вебмастер) требуют внешних API-ключей,
которых на P2 нет. Поэтому оба фактора вынесены за интерфейс-адаптер, а ДЕФОЛТ —
stub, возвращающий вердикт `deferred` (фактор не проверен — это НЕ `fail`, §schemas).

Реальные реализации (PageSpeed API / local Lighthouse; Bing/Яндекс creds) подключаются
позже без изменения оркестратора `audit_site` — он принимает адаптеры как зависимости.
Секреты приходят только из окружения/Lockbox, не в коде (§6.9).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from wizor.crawler.schemas import FactorVerdict


@runtime_checkable
class CoreWebVitalsAdapter(Protocol):
    """Оценивает Core Web Vitals сайта → `FactorVerdict` (factor='cwv')."""

    async def evaluate(self, site_url: str) -> FactorVerdict: ...


@runtime_checkable
class IndexabilityAdapter(Protocol):
    """Оценивает индексируемость (Bing/Яндекс) → `FactorVerdict` (factor='indexability')."""

    async def evaluate(self, site_url: str) -> FactorVerdict: ...


class StubCoreWebVitalsAdapter:
    """Дефолт: CWV не измеряется без API-ключа → `deferred` (форк #4)."""

    async def evaluate(self, site_url: str) -> FactorVerdict:
        return FactorVerdict(
            factor="cwv",
            verdict="deferred",
            detail="Core Web Vitals не измерены: не подключён источник "
            "(PageSpeed API / local Lighthouse) — требуется ключ founder'а.",
            data={"provider": None, "url": site_url},
        )


class StubIndexabilityAdapter:
    """Дефолт: индексируемость не проверяется без creds → `deferred` (форк #5)."""

    async def evaluate(self, site_url: str) -> FactorVerdict:
        return FactorVerdict(
            factor="indexability",
            verdict="deferred",
            detail="Индексируемость не проверена: не подключены Bing IndexNow / "
            "Яндекс.Вебмастер API — требуются учётные данные founder'а.",
            data={"provider": None, "url": site_url},
        )
