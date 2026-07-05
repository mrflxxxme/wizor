"""Unit: ScoringEngine — детерминизм (AC-1), компоненты (AC-3), границы (AC-5).

Чистая функция `score_audit`: сеть/БД не нужны. Момент времени фиксирован — расчёт
не зависит от часов (детерминизм). Все входы строятся из `weights.WEIGHTS`, чтобы тест
не хардкодил конкретные веса и переживал их калибровку (смена = новый SCORE_VERSION).
"""

from __future__ import annotations

import datetime

import pytest

from wizor.scoring.engine import ScoringEngine
from wizor.scoring.schemas import ScoreResult
from wizor.scoring.weights import SCORE_VERSION, WEIGHTS

_NOW = datetime.datetime(2026, 7, 5, 12, 0, tzinfo=datetime.UTC)
_SCORED_FACTORS = tuple(fw.factor for fw in WEIGHTS if fw.availability == "scored")


def _audit(verdict_by_factor: dict[str, str]) -> list[dict[str, object]]:
    """Собрать audit_summary в форме P2 из отображения ``factor → verdict``."""
    return [
        {"factor": factor, "verdict": verdict, "detail": "", "data": {}}
        for factor, verdict in verdict_by_factor.items()
    ]


def _score(audit: list[dict[str, object]]) -> ScoreResult:
    return ScoringEngine().score_audit(audit, calculated_at=_NOW)


def test_determinism_100_runs_identical() -> None:
    """AC-1: один вход, прогнанный 100 раз, даёт идентичный Score и компоненты."""
    audit = _audit({"robots_txt": "pass", "http_status": "warn", "json_ld": "fail", "faq": "pass"})
    results = [_score(audit) for _ in range(100)]

    scores = {r.score for r in results}
    assert len(scores) == 1  # ровно одно значение Score на 100 прогонов
    baseline = results[0].model_dump()
    assert all(r.model_dump() == baseline for r in results)


def test_components_expose_required_fields_ac3() -> None:
    """AC-3: по одному компоненту на взвешенный фактор с name/weight/value/verdict/description."""
    result = _score(_audit({"robots_txt": "pass"}))

    # Ровно факторы WEIGHTS в том же порядке (порядок раскрытия пользователю).
    assert [c.name for c in result.components] == [fw.factor for fw in WEIGHTS]
    for component in result.components:
        assert component.name
        assert component.weight > 0.0
        assert 0.0 <= component.value <= 1.0
        assert component.verdict in {"pass", "warn", "fail", "deferred"}
        assert component.description  # RU-пояснение непусто
        # contribution == weight * value (контракт schemas.ScoreComponent).
        assert component.contribution == component.weight * component.value


def test_empty_audit_scores_zero_ac5() -> None:
    """AC-5: пустой аудит (недоступный сайт) → Score в [0, 10], без деления на ноль."""
    result = _score([])
    assert result.score == 0.0
    assert 0.0 <= result.score <= 10.0


def test_all_fail_scores_low_ac5() -> None:
    """AC-5: все скорируемые факторы fail → Score в [0, 10]."""
    result = _score(_audit(dict.fromkeys(_SCORED_FACTORS, "fail")))
    assert 0.0 <= result.score <= 10.0


def test_all_pass_scores_high_ac5() -> None:
    """AC-5: идеальный сайт (все скорируемые pass) → Score ≥ 85 (deferred не мешает)."""
    result = _score(_audit(dict.fromkeys(_SCORED_FACTORS, "pass")))
    assert result.score >= 85.0


def test_all_deferred_no_divide_by_zero() -> None:
    """Все факторы deferred → знаменатель пуст → Score 0.0 (без ZeroDivisionError)."""
    result = _score(_audit({fw.factor: "deferred" for fw in WEIGHTS}))
    assert result.score == 0.0


def test_deferred_factors_do_not_penalise() -> None:
    """`deferred` нейтрален: идеальный сайт с deferred cwv/indexability всё равно = 100."""
    # Все scored=pass; deferred/future факторы отсутствуют или deferred → исключены.
    result = _score(_audit(dict.fromkeys(_SCORED_FACTORS, "pass")))
    assert result.score == 100.0
    assert result.score_version == SCORE_VERSION


def test_unknown_verdict_raises() -> None:
    """Мусорный вердикт во входе → ValueError (fail-fast; вход P2 ограничен Literal)."""
    with pytest.raises(ValueError, match="неизвестный вердикт"):
        _score([{"factor": "robots_txt", "verdict": "bogus", "detail": "", "data": {}}])
