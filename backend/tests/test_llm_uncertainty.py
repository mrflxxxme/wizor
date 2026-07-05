"""Unit: uncertainty-агрегация (AC-7) — N≥5 прогонов → {mean, ci_lower, ci_upper, n}.

Детерминированный вход (без mock'а сети): проверяется корректность t-доверительного
интервала и требование N≥5 (§6.7).
"""

from __future__ import annotations

import statistics
from math import sqrt
from typing import Any

import pytest

from wizor.llm_router.config import LLMRouterSettings
from wizor.llm_router.router import LLMRouter
from wizor.llm_router.schemas import LLMRequest, LLMResponse, Provider
from wizor.llm_router.uncertainty import MIN_RUNS, aggregate_uncertainty

# t-критическое для df=4 (N=5), доверие 95% — из таблицы Стьюдента.
_T_CRIT_DF4_95 = 2.776


# --- Базовая корректность интервала ---------------------------------------------------


def test_zero_variance_collapses_to_point() -> None:
    stats = aggregate_uncertainty([1.0, 1.0, 1.0, 1.0, 1.0])
    assert stats.mean == pytest.approx(1.0)
    assert stats.ci_lower == pytest.approx(1.0)
    assert stats.ci_upper == pytest.approx(1.0)
    assert stats.n == 5


def test_t_interval_matches_manual_formula() -> None:
    values = [0.2, 0.4, 0.6, 0.8, 1.0]
    stats = aggregate_uncertainty(values)
    expected_mean = 0.6
    expected_se = statistics.stdev(values) / sqrt(len(values))
    expected_margin = _T_CRIT_DF4_95 * expected_se

    assert stats.mean == pytest.approx(expected_mean)
    assert stats.ci_lower == pytest.approx(expected_mean - expected_margin, rel=1e-3)
    assert stats.ci_upper == pytest.approx(expected_mean + expected_margin, rel=1e-3)


def test_ci_brackets_mean() -> None:
    stats = aggregate_uncertainty([0.1, 0.3, 0.35, 0.5, 0.9, 0.7])
    assert stats.ci_lower <= stats.mean <= stats.ci_upper
    assert stats.n == 6


# --- §6.7: N<5 → отказ (не молчаливое ослабление честности) ----------------------------


def test_below_min_runs_raises() -> None:
    with pytest.raises(ValueError, match="N≥5"):
        aggregate_uncertainty([0.5, 0.5, 0.5, 0.5])


def test_min_runs_constant_is_five() -> None:
    assert MIN_RUNS == 5


# --- Интеграция: probe-путь роутера отдаёт uncertainty при 5 успешных прогонах ---------


class _ScriptedProvider:
    """Фейк: отдаёт заранее заданные тексты по очереди (детерминизм для CI-проверки)."""

    def __init__(self, provider: Provider, *, texts: list[str]) -> None:
        self.provider = provider
        self._texts = texts
        self.calls = 0

    async def complete(
        self, prompt: str, *, task_type: Any = "probe", **kwargs: Any
    ) -> LLMResponse:
        del prompt, kwargs
        text = self._texts[self.calls]
        self.calls += 1
        return LLMResponse(text=text, provider=self.provider, task_type=task_type, model="fake")


@pytest.mark.asyncio
async def test_router_probe_returns_uncertainty_over_five_runs() -> None:
    texts = ["0.2", "0.4", "0.6", "0.8", "1.0"]
    scripted = _ScriptedProvider("openai", texts=texts)
    router = LLMRouter(
        settings=LLMRouterSettings(_env_file=None, openai_api_key="k"),
        provider_factory=lambda _p: scripted,
    )
    result = await router.probe(
        LLMRequest(prompt="кто лидер?", task_type="probe", n_runs=5),
        score_fn=lambda r: float(r.text),
    )
    assert result.uncertainty is not None
    assert result.uncertainty.n == 5
    assert result.uncertainty.mean == pytest.approx(0.6)
    assert result.uncertainty.ci_lower < result.uncertainty.mean < result.uncertainty.ci_upper
