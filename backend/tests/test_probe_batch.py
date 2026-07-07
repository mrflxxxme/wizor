"""Unit: fault-isolation probe-батча (P5, AC-1/AC-6) + прокид per-site brand_terms (F1).

Проверяет чистый сборщик прогонов :func:`collect_probe_runs` с mock-раннером (БД не нужна):
сбой одного провайдера логируется как ``failed_model`` и НЕ роняет остальные три (AC-6);
батч из 4 моделей завершается и даёт положительный агрегат при частичном сбое (AC-1).
``egress`` §6.4 сохраняется даже на упавших прогонах иностранных моделей. Отдельно —
что per-site ``brand_terms`` доходят до КАЖДОГО ``run_prompt`` (без них метрики инертны) и
что :func:`_site_brand_terms` выводит вменяемые термы из URL.
"""

from __future__ import annotations

import datetime
from collections.abc import Sequence

import pytest

from wizor.metrics.engine import aggregate_visibility
from wizor.probe.schemas import FOREIGN_MODELS, ModelId, ProbeRun
from wizor.probe.tasks import (
    PROBE_MODELS,
    RUNS_PER_PROMPT,
    _site_brand_terms,
    collect_probe_runs,
)

_NOW = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


class _FakeRunner:
    """Mock probe-раннера: заданные модели всегда падают, прочие возвращают success.

    Записывает полученные ``brand_terms`` каждого вызова — проверяем прокид шва (F1).
    """

    def __init__(self, failing: set[ModelId]) -> None:
        self._failing = failing
        self.seen_brand_terms: list[tuple[str, ...]] = []

    async def run_prompt(
        self,
        *,
        prompt_id: str,
        prompt: str,
        model: ModelId,
        n_runs: int,
        brand_terms: Sequence[str],
    ) -> list[ProbeRun]:
        self.seen_brand_terms.append(tuple(brand_terms))
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

    runs, failed = await collect_probe_runs(runner, ["p0", "p1"], brand_terms=["acme"], now=_NOW)

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

    runs, failed = await collect_probe_runs(runner, ["p0"], brand_terms=["acme"], now=_NOW)

    assert failed == []
    assert len(runs) == len(PROBE_MODELS) * 1 * RUNS_PER_PROMPT
    assert RUNS_PER_PROMPT >= 5


@pytest.mark.asyncio
async def test_batch_survives_partial_failure_yields_metrics_ac1() -> None:
    """AC-1: батч не падает при сбое провайдера — 3 успешных дают положительный Score."""
    runner = _FakeRunner(failing={"perplexity"})

    runs, failed = await collect_probe_runs(runner, ["p0"], brand_terms=["acme"], now=_NOW)
    _aggregates, metrics = aggregate_visibility(runs, prompt_set_version=1)

    assert failed == ["perplexity"]
    assert metrics.visibility_score > 0.0
    assert metrics.n == len(PROBE_MODELS) * 1 * RUNS_PER_PROMPT - RUNS_PER_PROMPT


@pytest.mark.asyncio
async def test_brand_terms_flow_through_seam_f1() -> None:
    """F1: per-site brand_terms прокидываются в КАЖДЫЙ run_prompt (иначе метрики инертны)."""
    runner = _FakeRunner(failing=set())
    terms = ["acme", "acme.ru"]

    await collect_probe_runs(runner, ["p0", "p1"], brand_terms=terms, now=_NOW)

    # По одному вызову на (модель × промпт) — и каждый получил ровно те же per-site термы.
    assert len(runner.seen_brand_terms) == len(PROBE_MODELS) * 2
    assert all(seen == tuple(terms) for seen in runner.seen_brand_terms)


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.example.com/path?q=1", ["example", "example.com"]),
        ("https://example.ru", ["example", "example.ru"]),
        ("http://user:pass@shop.example.com:8443/", ["example", "shop.example.com"]),
        ("https://localhost", ["localhost"]),
        ("not-a-url", []),
    ],
)
def test_site_brand_terms_derivation_f1(url: str, expected: list[str]) -> None:
    """F1: _site_brand_terms выводит бренд-метку + хост из URL (чисто, без сети)."""
    assert _site_brand_terms(url) == expected
