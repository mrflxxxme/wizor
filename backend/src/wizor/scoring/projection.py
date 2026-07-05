"""Детерминированная Readiness-проекция (P3, T4).

`ProjectionEngine` отвечает на вопрос «насколько вырастет Score, если применить
конкретный фикс» — БЕЗ повторного краула. Метод: применить патч (целевой вердикт по
фактору) к КОПИИ `audit_summary` в памяти и пересчитать Score тем же
:class:`ScoringEngine`. Прирост ``delta_score = new − current`` (AC-4).

`Fix` — минимальный стаб-контракт интерфейса рекомендаций P6 (`fix_id + factor +
target_verdict`). P6 наполнит его реальными рекомендациями; здесь важно лишь, что
проекция детерминирована и не трогает исходный `audit_summary`.

Инвариант §6.5 сохраняется транзитивно: фикс на `llms_txt` (или любой фактор вне
`WEIGHTS`) даёт ``delta_score == 0`` — движок его не читает. Honest-forecast (§6.2):
проекция — детерминированный пересчёт сигнала готовности, НЕ гарантия Visibility-%.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from pydantic import BaseModel

from wizor.scoring.engine import ScoringEngine, index_verdicts
from wizor.scoring.schemas import ScoreProjection, Verdict
from wizor.scoring.weights import WEIGHTS

if TYPE_CHECKING:
    from datetime import datetime

# Вердикты, для которых имеет смысл предлагать фикс «довести до pass» (реально
# скорируемые сегодня и ещё не идеальные). `deferred`/отсутствующие факторы требуют
# ключа/экстрактора P6+ — не действенны как рекомендация в P3.
_IMPROVABLE_VERDICTS = ("warn", "fail")
_ROUND_NDIGITS = 4


class Fix(BaseModel):
    """Гипотетический фикс для Readiness-проекции (стаб-контракт рекомендаций P6)."""

    fix_id: str
    factor: str
    """Идентификатор аудит-фактора (== `crawler.FactorVerdict.factor`)."""
    target_verdict: Verdict
    """Вердикт, к которому фикс приводит фактор (обычно `pass`)."""
    description: str = ""


def derive_stub_fixes(audit_summary: Sequence[Mapping[str, object]]) -> list[Fix]:
    """Собрать детерминированный набор фиксов-кандидатов из текущего аудита (P3-стаб).

    Для каждого скорируемого фактора `WEIGHTS`, стоящего сегодня в `warn`/`fail`,
    предлагается фикс «довести до `pass`». Порядок = порядок `WEIGHTS` (детерминизм).
    P6 заменит этот вывод реальными рекомендациями с приоритетами.
    """
    verdict_by_factor = index_verdicts(audit_summary)
    fixes: list[Fix] = []
    for factor_weight in WEIGHTS:
        verdict = verdict_by_factor.get(factor_weight.factor)
        if verdict in _IMPROVABLE_VERDICTS:
            fixes.append(
                Fix(
                    fix_id=f"fix_{factor_weight.factor}",
                    factor=factor_weight.factor,
                    target_verdict="pass",
                    description=factor_weight.description,
                ),
            )
    return fixes


class ProjectionEngine:
    """Детерминированный пересчёт Score для набора гипотетических фиксов (AC-4)."""

    def __init__(self, engine: ScoringEngine | None = None) -> None:
        """Принимает :class:`ScoringEngine` (по умолчанию — новый) для пересчёта Score."""
        self._engine = engine or ScoringEngine()

    def project(
        self,
        audit_summary: Sequence[Mapping[str, object]],
        fixes: Sequence[Fix],
        *,
        calculated_at: datetime,
        site_url: str = "",
    ) -> list[ScoreProjection]:
        """Спроецировать прирост Score для каждого фикса (без краула, детерминированно).

        Текущий Score считается один раз; для каждого фикса патч применяется к КОПИИ
        `audit_summary` (исходный неизменен) и Score пересчитывается. Возвращает
        `ScoreProjection` (fix_id, delta_score, new_score) в порядке `fixes`.
        """
        current = self._engine.score_audit(
            audit_summary, calculated_at=calculated_at, site_url=site_url
        ).score
        projections: list[ScoreProjection] = []
        for fix in fixes:
            patched = _apply_fix(audit_summary, fix)
            new_score = self._engine.score_audit(
                patched, calculated_at=calculated_at, site_url=site_url
            ).score
            projections.append(
                ScoreProjection(
                    fix_id=fix.fix_id,
                    delta_score=round(new_score - current, _ROUND_NDIGITS),
                    new_score=new_score,
                    description=fix.description,
                ),
            )
        return projections


def _apply_fix(audit_summary: Sequence[Mapping[str, object]], fix: Fix) -> list[dict[str, object]]:
    """Вернуть КОПИЮ `audit_summary` с применённым фиксом (исходный не мутируется).

    Если фактор фикса присутствует — его вердикт заменяется на `target_verdict`; если
    отсутствует — добавляется новая запись. Каждая запись копируется (shallow) — расчёт
    не имеет побочных эффектов на вход (детерминизм повторного вызова).
    """
    patched: list[dict[str, object]] = []
    replaced = False
    for entry in audit_summary:
        new_entry = dict(entry)
        if new_entry.get("factor") == fix.factor:
            new_entry["verdict"] = fix.target_verdict
            replaced = True
        patched.append(new_entry)
    if not replaced:
        patched.append(
            {"factor": fix.factor, "verdict": fix.target_verdict, "detail": "", "data": {}},
        )
    return patched
