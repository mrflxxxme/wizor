"""Детерминированный движок Visibility-метрик (P5).

``aggregate_visibility`` — ЧИСТАЯ функция: ``list[ProbeRun]`` → ``(list[PromptModelAggregate],
VisibilityMetrics)``. Никакого I/O и часов внутри расчёта (детерминизм): момент времени
``calculated_at`` живёт в persistence-слое, а не здесь. Один и тот же вход даёт побайтово
один и тот же выход — тестируется на mock-прогонах.

**Компоненты Visibility (FR-2.4), каждый [0..1]:**

* ``coverage`` (Presence) = доля промптов, упомянутых хотя бы в одной модели (по успешным
  прогонам). «Промпт покрыт», если ∃ успешный прогон с ``mentioned=True``.
* ``sov`` (Share of Voice) = client / (client + competitor). **Конкурент-данных в P5 нет**
  → задокументированный fallback: ``sov = coverage`` (proxy присутствия). Истинный SoV с
  трекингом конкурентов приходит в поздней фазе; здесь SoV НЕ выдаётся за конкурентную долю.
* ``citation_rate`` = доля УСПЕШНЫХ прогонов с ``cited=True`` (клиент как источник/ссылка).
* ``stability`` (AC-7) = 1 − нормированная дисперсия ``mentioned`` между прогонами. Для
  булева сигнала дисперсия максимальна при p=0.5 (``p(1−p)=0.25``); нормируем на 0.25 →
  ``stability = 1 − 4·p·(1−p)``. Детерминированный mock (одинаковые ответы) → дисперсия 0 →
  ``stability = 1.0 > 0.8``. Итоговая stability = среднее по агрегатам промпт×модель.

**Композит (веса задокументированы, сумма = 1):**
``visibility_score = 100 · (0.40·coverage + 0.20·sov + 0.25·citation_rate + 0.15·stability)``
— presence доминирует; citation важнее шумовой стабильности. Итог ∈ [0..100].

**Полоса шума (CI, §6.2/§6.7 honest-forecast).** Per-run сигнал ``s_i = 0.6·mentioned +
0.4·cited`` (наблюдаемо на уровне одного прогона) сводится через
:func:`wizor.llm_router.uncertainty.aggregate_uncertainty` (t-интервал, N≥5). Из интервала
берётся полуширина (margin) и симметрично навешивается на композит: ``score ± margin·100``
(клампится в [0..100]). При нулевой дисперсии (детерминированный вход) полоса вырождается в
точку. При N<5 честный CI не заявляется — полоса схлопывается к score, а ``n`` несёт правду
(§6.7: улучшение заявляется только при N≥5 вне полосы).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from wizor.llm_router.uncertainty import MIN_RUNS, aggregate_uncertainty
from wizor.metrics.schemas import VisibilityComponents, VisibilityMetrics
from wizor.probe.schemas import ModelId, ProbeRun, PromptModelAggregate

# Веса композита Visibility (сумма = 1.0; presence доминирует). Единый источник — здесь.
_W_COVERAGE = 0.40
_W_SOV = 0.20
_W_CITATION = 0.25
_W_STABILITY = 0.15

# Веса per-run сигнала для полосы шума (наблюдаемо на уровне прогона; сумма = 1.0).
_SIGNAL_W_MENTION = 0.6
_SIGNAL_W_CITATION = 0.4

# Максимум дисперсии булева сигнала (p(1−p) при p=0.5) — нормировщик stability.
_MAX_BERNOULLI_VAR = 0.25

# Число знаков округления — гасит float-шум, оставаясь детерминированным.
_ROUND_NDIGITS = 4


def _stability_from_mentions(mentions: Sequence[bool]) -> float:
    """1 − нормированная дисперсия булева ``mentioned`` между прогонами (AC-7).

    Пусто → 0.0 (нет данных — не заявляем стабильность). Одинаковые значения → 1.0.
    """
    if not mentions:
        return 0.0
    p = sum(1.0 for m in mentions if m) / len(mentions)
    normalized_var = (p * (1.0 - p)) / _MAX_BERNOULLI_VAR
    return round(1.0 - normalized_var, _ROUND_NDIGITS)


def _build_aggregates(runs: Sequence[ProbeRun]) -> list[PromptModelAggregate]:
    """Сгруппировать прогоны по (prompt_id, model) → детерминированные агрегаты.

    ``mention_rate``/``citation_rate`` считаются по УСПЕШНЫМ прогонам (``error is None``);
    ``stability`` — по ``mentioned`` УСПЕШНЫХ прогонов. Порядок агрегатов детерминирован
    (сортировка по ключу).
    """
    grouped: dict[tuple[str, ModelId], list[ProbeRun]] = defaultdict(list)
    for run in runs:
        grouped[(run.prompt_id, run.model)].append(run)

    aggregates: list[PromptModelAggregate] = []
    for (prompt_id, model), group in sorted(grouped.items()):
        successes = [r for r in group if r.error is None]
        n_success = len(successes)
        mentions = [r.mentioned for r in successes]
        mention_rate = (sum(1.0 for m in mentions if m) / n_success) if n_success else 0.0
        citation_rate = (sum(1.0 for r in successes if r.cited) / n_success) if n_success else 0.0
        aggregates.append(
            PromptModelAggregate(
                prompt_id=prompt_id,
                model=model,
                n=len(group),
                n_success=n_success,
                mention_rate=round(mention_rate, _ROUND_NDIGITS),
                citation_rate=round(citation_rate, _ROUND_NDIGITS),
                stability=_stability_from_mentions(mentions),
            )
        )
    return aggregates


def _coverage(runs: Sequence[ProbeRun]) -> float:
    """Доля промптов, упомянутых хотя бы в одной модели (по успешным прогонам)."""
    prompts: set[str] = set()
    covered: set[str] = set()
    for run in runs:
        if run.error is not None:
            continue
        prompts.add(run.prompt_id)
        if run.mentioned:
            covered.add(run.prompt_id)
    if not prompts:
        return 0.0
    return round(len(covered) / len(prompts), _ROUND_NDIGITS)


def _noise_band(successes: Sequence[ProbeRun], visibility_score: float) -> tuple[float, float, int]:
    """Полоса шума вокруг композита: ``score ± margin·100`` (клампится в [0..100]).

    Margin — полуширина t-доверительного интервала per-run сигнала (N≥5, §6.7). N<5 →
    полоса схлопывается к точке (честный CI не заявляется). Возвращает ``(ci_lower,
    ci_upper, n)``, где ``n`` — число успешных прогонов в основе.
    """
    signals = [
        _SIGNAL_W_MENTION * float(r.mentioned) + _SIGNAL_W_CITATION * float(r.cited)
        for r in successes
    ]
    n = len(signals)
    if n < MIN_RUNS:
        return visibility_score, visibility_score, n
    stats = aggregate_uncertainty(signals)
    half_width = ((stats.ci_upper - stats.ci_lower) / 2.0) * 100.0
    ci_lower = max(0.0, round(visibility_score - half_width, _ROUND_NDIGITS))
    ci_upper = min(100.0, round(visibility_score + half_width, _ROUND_NDIGITS))
    return ci_lower, ci_upper, n


def aggregate_visibility(
    runs: Sequence[ProbeRun],
    *,
    prompt_set_version: int | None = None,
) -> tuple[list[PromptModelAggregate], VisibilityMetrics]:
    """Свести probe-прогоны в агрегаты промпт×модель и композит Visibility (чистая функция).

    Возвращает ``(aggregates, metrics)``. Пустой вход → безопасный ноль (score 0, компоненты
    0, ``n=0``) без деления на ноль. Момент расчёта НЕ читается здесь (детерминизм) —
    ``calculated_at`` присваивается в persistence-слое.
    """
    aggregates = _build_aggregates(runs)
    successes = [r for r in runs if r.error is None]

    coverage = _coverage(runs)
    sov = coverage  # P5 fallback: нет конкурент-данных → proxy присутствия (см. докстринг).
    n_success = len(successes)
    citation_rate = (
        round(sum(1.0 for r in successes if r.cited) / n_success, _ROUND_NDIGITS)
        if n_success
        else 0.0
    )
    stability = (
        round(sum(a.stability for a in aggregates) / len(aggregates), _ROUND_NDIGITS)
        if aggregates
        else 0.0
    )

    components = VisibilityComponents(
        coverage=coverage,
        sov=sov,
        citation_rate=citation_rate,
        stability=stability,
        # P5: конкурент-данных нет → sov это coverage-прокси, а не реальная доля (§6.2).
        has_competitor_data=False,
    )
    visibility_score = round(
        100.0
        * (
            _W_COVERAGE * coverage
            + _W_SOV * sov
            + _W_CITATION * citation_rate
            + _W_STABILITY * stability
        ),
        _ROUND_NDIGITS,
    )
    ci_lower, ci_upper, n = _noise_band(successes, visibility_score)

    metrics = VisibilityMetrics(
        visibility_score=visibility_score,
        components=components,
        ci_lower=ci_lower,
        ci_upper=ci_upper,
        n=n,
        prompt_set_version=prompt_set_version,
    )
    return aggregates, metrics
