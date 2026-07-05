"""``LLMRouter`` — фасад provider-agnostic роутера (P4).

Оркестрирует: `resolve_route` (§6.6 RU-default / §6.4 probe-geo) → `assert_geo`
(структурный предохранитель) → выбор доступного провайдера с RU-fallback-цепочкой →
`CostGuard` (AC-6) → адаптер провайдера с ретраем (AC-5). Даёт две точки входа:

* ``complete(req)`` — одиночный вызов (content_gen/schema_gen/batch).
* ``probe(req, score_fn)`` — probe-канал: N≥5 прогонов через зарубежную ноду, сбой одного
  прогона НЕ роняет остальные (fault isolation, AC-5), агрегируется uncertainty (AC-7).

Провайдеры создаются через инъектируемую фабрику ``provider_factory`` (по умолчанию —
`providers.make_provider` из config): тесты подменяют её фейками/mock-транспортом без сети.
Никакого тихого иностранного fallback: если RU-цепочка недоступна для ПД-задачи —
:class:`NoAvailableProviderError`, а не подмена иностранным (§6.6, system-prompt failure mode).
"""

from __future__ import annotations

from collections.abc import Callable

import structlog

from wizor.llm_router.config import LLMRouterSettings, get_llm_settings
from wizor.llm_router.cost_guard import (
    CostBudgetExceededError,
    CostGuard,
    estimate_cost_usd,
)
from wizor.llm_router.providers import (
    LLMProvider,
    ProviderError,
    make_provider,
)
from wizor.llm_router.routing import (
    RouteDecision,
    assert_geo,
    resolve_route,
    ru_default_chain,
)
from wizor.llm_router.schemas import (
    LLMRequest,
    LLMResponse,
    ProbeResult,
    Provider,
    ProviderConfigDTO,
    TaskType,
)
from wizor.llm_router.uncertainty import MIN_RUNS, aggregate_uncertainty

logger = structlog.get_logger(__name__)

# Тип инъектируемой фабрики провайдеров (config-driven по умолчанию, фейки в тестах).
ProviderFactory = Callable[[Provider], LLMProvider]

# Тип функции извлечения скалярного сигнала из ответа probe (для uncertainty).
ScoreFn = Callable[[LLMResponse], float]


def _default_score(response: LLMResponse) -> float:
    """Дефолтный сигнал probe: presence — 1.0 если ответ непустой, иначе 0.0.

    Реальные метрики (mention/SoV/citation) считает metrics-контекст P5; здесь —
    нейтральный placeholder, чтобы uncertainty-канал был замкнут уже в P4.
    """
    return 1.0 if response.text.strip() else 0.0


class NoAvailableProviderError(RuntimeError):
    """Ни один допустимый провайдер маршрута недоступен (НЕ тихий иностранный fallback)."""


class LLMRouter:
    """Единый вход всех LLM-вызовов платформы (probe, FAQ-gen, schema-gen, batch)."""

    def __init__(
        self,
        *,
        settings: LLMRouterSettings | None = None,
        provider_factory: ProviderFactory | None = None,
    ) -> None:
        self._settings = settings or get_llm_settings()
        # Дефолтная фабрика: config-driven адаптеры (ключи из Lockbox/env, §6.9).
        self._factory: ProviderFactory = provider_factory or (
            lambda provider: make_provider(provider, self._settings)
        )

    def _new_cost_guard(self, req: LLMRequest) -> CostGuard:
        """Свежий per-task cost-guard из настроек (числа — cost-budget.yaml §3.4)."""
        return CostGuard(
            soft_cap_usd=self._settings.llm_per_task_soft_usd,
            hard_cap_usd=self._settings.llm_per_task_hard_usd,
            task_type=req.task_type,
            tenant_id=req.tenant_id,
        )

    def _provider_chain(self, decision: RouteDecision) -> tuple[Provider, ...]:
        """Цепочка провайдеров для попытки: RU-default получает fallback GigaChat→YandexGPT.

        Только для дефолтного RU-маршрута ПД-задачи (не для явного override и не для
        иностранных/OSS). Цепочка НИКОГДА не содержит иностранного провайдера (§6.6).
        """
        if decision.reason in {"default", "foreign_override_refused_pd"} and decision.contains_pd:
            # ПД-задача по RU-дефолту: primary→secondary среди RU-провайдеров.
            chain = ru_default_chain()
            if decision.provider in chain:
                # Начать с выбранного, затем остальные RU по порядку (без дублей).
                rest = tuple(p for p in chain if p != decision.provider)
                return (decision.provider, *rest)
        return (decision.provider,)

    def _pick_available(self, decision: RouteDecision) -> tuple[Provider, LLMProvider]:
        """Выбрать первый сконфигурированный провайдер цепочки; иначе явная ошибка.

        НЕТ тихого иностранного fallback: если вся RU-цепочка недоступна для ПД-задачи —
        :class:`NoAvailableProviderError` (system-prompt: не молчаливый иностранный fallback).
        """
        chain = self._provider_chain(decision)
        for provider in chain:
            if self._settings.is_configured(provider):
                return provider, self._factory(provider)
        msg = (
            f"нет доступного провайдера для задачи {decision.reason!r} "
            f"(цепочка {chain}); §6.6: тихий иностранный fallback запрещён."
        )
        raise NoAvailableProviderError(msg)

    async def preview_route(
        self,
        *,
        task_type: TaskType,
        tenant_configs: list[ProviderConfigDTO],
        provider_override: Provider | None,
    ) -> Provider:
        """Превью (AC-1/AC-2): какой провайдер БЫЛ БЫ выбран — без вызова провайдера.

        Делегирует чистому `resolve_route` (RU-default + §6.6 refuse-foreign-on-PD +
        §6.4 probe-geo). Async — контракт preview-эндпоинта (`_RoutingPreview`, `await`).
        `tenant_configs` пока не сужает выбор (правил по task_type + override достаточно
        для AC-1/AC-2); параметр зарезервирован под tenant-level enable/disable провайдеров.
        """
        _ = tenant_configs
        decision = resolve_route(
            LLMRequest(prompt="", task_type=task_type, provider_override=provider_override)
        )
        return decision.provider

    async def complete(self, req: LLMRequest) -> LLMResponse:
        """Одиночный вызов: маршрут → geo-guard → cost-guard → провайдер (с ретраем).

        Порядок гарантирует §6.6 (RU-default, foreign-override на ПД отклонён в
        `resolve_route`) и §6.4 (`assert_geo`). Бюджет проверяется до и после вызова (AC-6).
        """
        decision = resolve_route(req)
        assert_geo(decision)  # §6.4/NFR-2: инопровайдер ⇒ только зарубежная нода
        provider_name, provider = self._pick_available(decision)

        cost_guard = self._new_cost_guard(req)
        cost_guard.pre_authorize(estimate_cost_usd(req.prompt, provider_name))

        logger.info(
            "llm.route.selected",
            task_type=req.task_type,
            tenant_id=req.tenant_id,
            provider=provider_name,
            egress=decision.egress,
            reason=decision.reason,
            refused_override=decision.refused_override,
        )
        response = await provider.complete(req.prompt, task_type=req.task_type)
        cost_guard.record(response.cost_usd)
        return response

    async def probe(
        self,
        req: LLMRequest,
        *,
        score_fn: ScoreFn | None = None,
    ) -> ProbeResult:
        """Probe-канал: N≥5 прогонов через зарубежную ноду, fault-isolation, uncertainty.

        §6.4/NFR-2: `assert_geo` гарантирует зарубежный egress для инопровайдера. Сбой
        одного прогона (таймаут/ошибка провайдера) логируется и НЕ роняет остальные (AC-5).
        Стоимость аккумулируется по прогонам; hard-пробитие отменяет остаток (AC-6).
        Если успешных прогонов ≥ N_min — считается t-доверительный интервал (AC-7).
        """
        decision = resolve_route(req)
        assert_geo(decision)
        provider_name, provider = self._pick_available(decision)
        scorer = score_fn or _default_score

        n_runs = max(req.n_runs, MIN_RUNS)  # §6.7: probe всегда ≥5 прогонов
        cost_guard = self._new_cost_guard(req)
        responses: list[LLMResponse] = []

        for run_idx in range(n_runs):
            try:
                cost_guard.pre_authorize(estimate_cost_usd(req.prompt, provider_name))
                response = await provider.complete(req.prompt, task_type="probe")
                cost_guard.record(response.cost_usd)
            except CostBudgetExceededError:
                # Бюджет пробит — отменяем ОСТАВШИЕСЯ прогоны (уже собранные сохраняем).
                logger.warning(
                    "llm.probe.cost_cancelled",
                    tenant_id=req.tenant_id,
                    provider=provider_name,
                    completed_runs=len(responses),
                )
                break
            except ProviderError as exc:
                # Fault isolation (AC-5): один провал не роняет батч probe-прогонов.
                logger.warning(
                    "llm.probe.run_failed",
                    tenant_id=req.tenant_id,
                    provider=provider_name,
                    run_idx=run_idx,
                    error=str(exc),
                )
                continue
            responses.append(response)

        uncertainty = None
        if len(responses) >= MIN_RUNS:
            uncertainty = aggregate_uncertainty([scorer(r) for r in responses])
        return ProbeResult(responses=responses, uncertainty=uncertainty)
