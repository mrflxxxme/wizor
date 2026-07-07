"""Unit: fault-isolation probe-батча (P5, AC-1/AC-6).

Проверяет чистый сборщик прогонов :func:`collect_probe_runs` с mock-раннером (БД не нужна):
сбой одного провайдера логируется как ``failed_model`` и НЕ роняет остальные три (AC-6);
батч из 4 моделей завершается и даёт положительный агрегат при частичном сбое (AC-1).
``egress`` §6.4 сохраняется даже на упавших прогонах иностранных моделей.
"""

from __future__ import annotations

import datetime

import pytest

from wizor.metrics.engine import aggregate_visibility
from wizor.probe.schemas import FOREIGN_MODELS, ModelId, ProbeRun
from wizor.probe.tasks import PROBE_MODELS, RUNS_PER_PROMPT, collect_probe_runs

_NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


class _FakeRunner:
    """Mock probe-раннера: заданные модели всегда падают, прочие возвращают success."""

    def __init__(self, failing: set[ModelId]) -> None:
        self._failing = failing

    async def run_prompt(
        self, *, prompt_id: str, prompt: str, model: ModelId, n_runs: int
    ) -> list[ProbeRun]:
        if model in self._failing:
            msg = f"provider {model} down"
            raise RuntimeError(msg)  # wholesale-сбой → задача синтезирует N error-runs (AC-6)
        return [
            ProbeRun(
                prompt_id=prompt_id,
                model=model,
                run_index=i,
                raw_response=f"{prompt}:{i}",
                mentioned=True,
                cited=True,
                egress="foreign" if model in FOREIGN_MODELS else "ru",
                run_at=_NOW,
                error=None,
            )
            for i in range(n_runs)
        ]


@pytest.mark.asyncio
async def test_one_provider_fails_others_survive_ac6() -> None:
    """AC-6: 100% сбой одного провайдера → он в failed_models, остальные успешны."""
    runner = _FakeRunner(failing={"chatgpt"})

    runs, failed = await collect_probe_runs(runner, ["p0", "p1"], now=_NOW)

    assert failed == ["chatgpt"]
    assert len(runs) == len(PROBE_MODELS) * 2 * RUNS_PER_PROMPT
    chatgpt_runs = [r for r in runs if r.model == "chatgpt"]
    assert chatgpt_runs
    assert all(r.error is not None for r in chatgpt_runs)
    # §6.4: даже упавший прогон иностранной модели помечен egress='foreign', не 'ru'.
    assert all(r.egress == "foreign" for r in chatgpt_runs)
    other_runs = [r for r in runs if r.model != "chatgpt"]
    assert all(r.error is None for r in other_runs)


@pytest.mark.asyncio
async def test_all_success_no_failed_models() -> None:
    """Все модели успешны → пустой failed_models, N≥5 прогонов на промпт×модель."""
    runner = _FakeRunner(failing=set())

    runs, failed = await collect_probe_runs(runner, ["p0"], now=_NOW)

    assert failed == []
    assert len(runs) == len(PROBE_MODELS) * 1 * RUNS_PER_PROMPT
    assert RUNS_PER_PROMPT >= 5


@pytest.mark.asyncio
async def test_batch_survives_partial_failure_yields_metrics_ac1() -> None:
    """AC-1: батч не падает при сбое провайдера — 3 успешных дают положительный Score."""
    runner = _FakeRunner(failing={"perplexity"})

    runs, failed = await collect_probe_runs(runner, ["p0"], now=_NOW)
    _aggregates, metrics = aggregate_visibility(runs, prompt_set_version=1)

    assert failed == ["perplexity"]
    assert metrics.visibility_score > 0.0
    assert metrics.n == len(PROBE_MODELS) * 1 * RUNS_PER_PROMPT - RUNS_PER_PROMPT
