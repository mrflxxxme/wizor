"""Unit: чистый движок Visibility-метрик (P5, T5).

Проверяет форму агрегата (AC-4), stability>0.8 на детерминированных прогонах (AC-7),
детерминизм (один вход → один выход), безопасный ноль на пустом входе и исключение
упавших прогонов из основы CI. БД не требуется — движок чист.
"""

from __future__ import annotations

import datetime

import pytest

from wizor.metrics.engine import aggregate_visibility
from wizor.metrics.schemas import VisibilityMetrics
from wizor.probe.schemas import ModelId, ProbeRun

_FIXED_AT = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _run(
    prompt_id: str,
    run_index: int,
    *,
    mentioned: bool,
    cited: bool,
    model: ModelId = "alice_yandex",
    error: str | None = None,
) -> ProbeRun:
    """Собрать один ``ProbeRun`` (egress 'ru' — RU-модель по умолчанию)."""
    return ProbeRun(
        prompt_id=prompt_id,
        model=model,
        run_index=run_index,
        raw_response="response",
        mentioned=mentioned,
        cited=cited,
        egress="ru",
        run_at=_FIXED_AT,
        error=error,
    )


def test_aggregate_shape_ac4() -> None:
    """AC-4: агрегат несёт score[0..100], 4 компонента[0..1], CI, n, версию."""
    runs = [_run("0", i, mentioned=(i % 2 == 0), cited=(i == 0)) for i in range(6)]

    aggregates, metrics = aggregate_visibility(runs, prompt_set_version=2)

    assert isinstance(metrics, VisibilityMetrics)
    assert 0.0 <= metrics.visibility_score <= 100.0
    c = metrics.components
    for value in (c.coverage, c.sov, c.citation_rate, c.stability):
        assert 0.0 <= value <= 1.0
    assert metrics.n == 6
    assert metrics.prompt_set_version == 2
    # Полоса шума окружает композит (§6.7): ci_lower ≤ score ≤ ci_upper.
    assert metrics.ci_lower <= metrics.visibility_score <= metrics.ci_upper
    assert len(aggregates) == 1
    assert aggregates[0].prompt_id == "0"
    assert aggregates[0].n == 6


def test_stability_gt_08_on_deterministic_runs_ac7() -> None:
    """AC-7: детерминированный mock (одинаковые ответы) → stability≈1.0 (>0.8), CI = точка."""
    runs = [
        _run(str(prompt), i, mentioned=True, cited=True) for prompt in range(2) for i in range(5)
    ]

    _aggregates, metrics = aggregate_visibility(runs)

    assert metrics.components.stability > 0.8
    assert metrics.components.stability == pytest.approx(1.0)
    # Нулевая дисперсия → полоса шума вырождается в точку на композите.
    assert metrics.ci_lower == metrics.ci_upper == metrics.visibility_score


def test_deterministic_same_input_same_output() -> None:
    """Детерминизм: один и тот же вход даёт побайтово идентичный выход."""
    runs = [_run("0", i, mentioned=(i < 3), cited=(i < 2)) for i in range(5)]

    first = aggregate_visibility(runs, prompt_set_version=1)
    second = aggregate_visibility(runs, prompt_set_version=1)

    assert first == second


def test_empty_input_is_safe_zero() -> None:
    """Пустой вход → безопасный ноль без деления на ноль."""
    aggregates, metrics = aggregate_visibility([])

    assert aggregates == []
    assert metrics.visibility_score == 0.0
    assert metrics.n == 0
    assert metrics.components.coverage == 0.0
    assert metrics.ci_lower == 0.0
    assert metrics.ci_upper == 0.0


def test_failed_runs_excluded_from_success_basis() -> None:
    """Упавший прогон хранится в ``n``, но исключён из успехов и основы CI (fault-isolation)."""
    runs = [_run("0", i, mentioned=True, cited=True) for i in range(5)]
    runs.append(_run("0", 5, mentioned=True, cited=True, error="provider down"))

    aggregates, metrics = aggregate_visibility(runs)

    assert aggregates[0].n == 6
    assert aggregates[0].n_success == 5
    assert metrics.n == 5  # только успешные прогоны — основа CI (§6.7)


def test_sov_is_coverage_proxy_labeled_p5_f2() -> None:
    """F2 (§6.2 honest-forecast): в P5 sov — coverage-прокси, has_competitor_data=False."""
    runs = [_run("0", i, mentioned=(i % 2 == 0), cited=(i == 0)) for i in range(6)]

    _aggregates, metrics = aggregate_visibility(runs)

    # Флаг честности: конкурент-данных в P5 нет → фронт не выдаёт прокси за реальную долю.
    assert metrics.components.has_competitor_data is False
    # sov в точности равен coverage (задокументированный P5-fallback движка).
    assert metrics.components.sov == metrics.components.coverage
