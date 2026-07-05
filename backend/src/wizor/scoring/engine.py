"""Детерминированный движок AI-Readiness Score (P3, T2).

`ScoringEngine.score_audit` — ЧИСТАЯ функция: `audit_summary` (список
`{factor, verdict, detail, data}` из `crawler.CrawlResultRow.audit_summary_json`)
→ :class:`wizor.scoring.schemas.ScoreResult`. Никакого I/O и часов внутри расчёта —
момент времени `calculated_at` инъектируется вызывающей стороной (детерминизм, AC-1).

Формула (см. `WEIGHTS.md` §4): для каждого взвешенного фактора берём вердикт,
нормируем в [0..1] (`normalize_verdict`), вклад = `weight × value`. `deferred`-факторы
(нет ключа/экстрактора) исключаются И из числителя, И из знаменателя (`is_scored`) —
нейтрально, без штрафа. Итог: ``Score = 100 × Σвклад / Σвес(scored)``; пусто/всё
deferred → 0 (без деления на ноль).

Инвариант §6.5: движок джойнит `audit_summary` только с `weights.WEIGHTS`. `llms_txt`
структурно отсутствует в `WEIGHTS`, поэтому его сигнал в `audit_summary` НИКОГДА не
читается и не может поднять Score (AC-2). Порядок компонентов = порядок `WEIGHTS`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, cast

from wizor.scoring.schemas import ScoreComponent, ScoreResult, Verdict
from wizor.scoring.weights import (
    SCORE_VERSION,
    WEIGHTS,
    is_scored,
    normalize_verdict,
)

if TYPE_CHECKING:
    from datetime import datetime

# Отсутствие фактора в audit_summary (future-факторы entity_graph/recency, которые P2
# ещё не эмитит) трактуется как `deferred` — нейтрально исключается из знаменателя.
_MISSING_VERDICT = "deferred"

# Число знаков округления Score/вкладов — гасит float-шум, оставаясь детерминированным.
_ROUND_NDIGITS = 4


def index_verdicts(audit_summary: Sequence[Mapping[str, object]]) -> dict[str, str]:
    """Свести `audit_summary` к отображению ``factor → verdict`` (строки).

    Пропускает записи без строковых `factor`/`verdict` (мусор во входе игнорируется, а
    не роняет расчёт). Дубликаты фактора: побеждает последняя запись — детерминированно
    относительно порядка входа. Общий хелпер для движка и `ProjectionEngine`.
    """
    index: dict[str, str] = {}
    for entry in audit_summary:
        factor = entry.get("factor")
        verdict = entry.get("verdict")
        if isinstance(factor, str) and isinstance(verdict, str):
            index[factor] = verdict
    return index


class ScoringEngine:
    """Чистый детерминированный калькулятор AI-Readiness Score (без состояния)."""

    def score_audit(
        self,
        audit_summary: Sequence[Mapping[str, object]],
        *,
        calculated_at: datetime,
        site_url: str = "",
    ) -> ScoreResult:
        """Рассчитать Score поверх `audit_summary` (чистая функция, AC-1).

        `calculated_at` инъектируется (часы вне расчёта). Для каждого фактора `WEIGHTS`
        эмитится ровно один :class:`ScoreComponent` (в т.ч. для `deferred` — с value 0 и
        нулевым вкладом, для прозрачности AC-3). `deferred` исключается из знаменателя.
        Неизвестный вердикт во входе → `ValueError` (fail-fast: вход из P2 ограничен
        Literal). Пустой/полностью deferred аудит → Score 0 без деления на ноль.
        """
        verdict_by_factor = index_verdicts(audit_summary)
        components: list[ScoreComponent] = []
        numerator = 0.0
        scored_weight = 0.0

        for factor_weight in WEIGHTS:
            verdict = verdict_by_factor.get(factor_weight.factor, _MISSING_VERDICT)
            value = normalize_verdict(verdict)  # валидация: unknown → ValueError
            contribution = factor_weight.weight * value
            components.append(
                ScoreComponent(
                    name=factor_weight.factor,
                    layer=factor_weight.layer,
                    weight=factor_weight.weight,
                    value=value,
                    verdict=cast("Verdict", verdict),
                    contribution=contribution,
                    description=factor_weight.description,
                ),
            )
            if is_scored(verdict):
                numerator += contribution
                scored_weight += factor_weight.weight

        score = 0.0 if scored_weight == 0.0 else 100.0 * numerator / scored_weight
        return ScoreResult(
            site_url=site_url,
            score=round(score, _ROUND_NDIGITS),
            score_version=SCORE_VERSION,
            components=components,
            projection=[],
            calculated_at=calculated_at,
        )
