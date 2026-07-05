"""Unit: cost-guard (AC-6) — soft/hard per-task бюджет; пробитие hard отменяет задачу."""

from __future__ import annotations

from typing import Any

import pytest

from wizor.llm_router.config import LLMRouterSettings
from wizor.llm_router.cost_guard import (
    CostBudgetExceededError,
    CostGuard,
    estimate_cost_usd,
)
from wizor.llm_router.router import LLMRouter
from wizor.llm_router.schemas import LLMRequest, LLMResponse, Provider


def _guard(**overrides: Any) -> CostGuard:
    params: dict[str, Any] = {"soft_cap_usd": 0.40, "hard_cap_usd": 1.50, "task_type": "batch"}
    params.update(overrides)
    return CostGuard(**params)


# --- pre_authorize: прогноз выше hard → отмена ----------------------------------------


def test_pre_authorize_over_hard_cancels() -> None:
    guard = _guard()
    with pytest.raises(CostBudgetExceededError):
        guard.pre_authorize(2.0)


def test_pre_authorize_over_soft_under_hard_passes() -> None:
    guard = _guard()
    guard.pre_authorize(0.9)  # выше soft (0.40), ниже hard (1.50) → warning, но без raise
    assert guard.spent_usd == 0.0  # pre_authorize ничего не списывает


def test_pre_authorize_under_soft_passes() -> None:
    guard = _guard()
    guard.pre_authorize(0.1)
    assert guard.spent_usd == 0.0


# --- record: накопление фактической стоимости; пробитие hard → отмена ------------------


def test_record_accumulates_and_breaches_hard() -> None:
    guard = _guard()
    guard.record(1.0)
    assert guard.spent_usd == 1.0
    with pytest.raises(CostBudgetExceededError):
        guard.record(0.6)  # 1.0 + 0.6 = 1.6 > 1.5 → отмена


# --- Оценка стоимости положительна и растёт с N ---------------------------------------


def test_estimate_cost_positive_and_scales_with_runs() -> None:
    single = estimate_cost_usd("тестовый промпт", "openai", n_runs=1)
    many = estimate_cost_usd("тестовый промпт", "openai", n_runs=5)
    assert single > 0
    assert many > single


def test_estimate_oss_cheaper_than_foreign() -> None:
    prompt = "одинаковый промпт для сравнения"
    assert estimate_cost_usd(prompt, "vllm") < estimate_cost_usd(prompt, "openai")


# --- Интеграция с роутером: фактическая стоимость выше hard отменяет задачу -------------


class _CostlyProvider:
    def __init__(self, provider: Provider, *, cost: float) -> None:
        self.provider = provider
        self._cost = cost

    async def complete(
        self, prompt: str, *, task_type: Any = "batch", **kwargs: Any
    ) -> LLMResponse:
        del prompt, kwargs
        return LLMResponse(
            text="ok",
            provider=self.provider,
            task_type=task_type,
            model="fake",
            cost_usd=self._cost,
        )


def _settings() -> LLMRouterSettings:
    return LLMRouterSettings(_env_file=None, vllm_base_url="http://vllm:8000/v1")


@pytest.mark.asyncio
async def test_router_complete_cancels_on_hard_cost_breach() -> None:
    router = LLMRouter(
        settings=_settings(),
        provider_factory=lambda p: _CostlyProvider(p, cost=5.0),
    )
    with pytest.raises(CostBudgetExceededError):
        await router.complete(LLMRequest(prompt="батч", task_type="batch"))


@pytest.mark.asyncio
async def test_router_probe_stops_runs_when_budget_exhausted() -> None:
    # Каждый прогон стоит 1.0; hard=1.5 → второй прогон пробивает бюджет, остаток отменён.
    router = LLMRouter(
        settings=LLMRouterSettings(_env_file=None, openai_api_key="k"),
        provider_factory=lambda p: _CostlyProvider(p, cost=1.0),
    )
    result = await router.probe(LLMRequest(prompt="x", task_type="probe", n_runs=5))
    assert len(result.responses) == 1  # только первый прогон уложился в бюджет
    assert result.uncertainty is None
