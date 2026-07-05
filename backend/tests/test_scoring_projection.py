"""Unit: ProjectionEngine — Readiness-проекция (AC-4).

Фикс fail→pass даёт `delta_score > 0` и корректный `new_score`; пересчёт без краула,
детерминирован; исходный `audit_summary` не мутируется. Инвариант §6.5 транзитивно:
фикс на llms.txt (вне WEIGHTS) → delta 0.
"""

from __future__ import annotations

import datetime

from wizor.scoring.engine import ScoringEngine
from wizor.scoring.projection import Fix, ProjectionEngine, derive_stub_fixes

_NOW = datetime.datetime(2026, 7, 5, 12, 0, tzinfo=datetime.UTC)
_ENGINE = ScoringEngine()
_PROJECTION = ProjectionEngine(_ENGINE)


def _audit(verdict_by_factor: dict[str, str]) -> list[dict[str, object]]:
    return [
        {"factor": factor, "verdict": verdict, "detail": "", "data": {}}
        for factor, verdict in verdict_by_factor.items()
    ]


def test_fix_fail_to_pass_raises_score_ac4() -> None:
    """AC-4: фикс faq fail→pass → delta_score > 0 и new_score = Score с применённым патчем."""
    audit = _audit({"robots_txt": "pass", "json_ld": "pass", "faq": "fail"})
    fix = Fix(fix_id="fix_faq", factor="faq", target_verdict="pass")

    [projection] = _PROJECTION.project(audit, [fix], calculated_at=_NOW)

    expected_new = _ENGINE.score_audit(
        _audit({"robots_txt": "pass", "json_ld": "pass", "faq": "pass"}),
        calculated_at=_NOW,
    ).score
    current = _ENGINE.score_audit(audit, calculated_at=_NOW).score

    assert projection.fix_id == "fix_faq"
    assert projection.new_score == expected_new
    assert projection.delta_score > 0.0
    assert projection.delta_score == round(expected_new - current, 4)


def test_projection_is_deterministic() -> None:
    """Одни и те же вход+фиксы → идентичные проекции на повторных вызовах."""
    audit = _audit({"faq": "warn", "json_ld": "fail", "robots_txt": "pass"})
    fixes = derive_stub_fixes(audit)

    first = _PROJECTION.project(audit, fixes, calculated_at=_NOW)
    second = _PROJECTION.project(audit, fixes, calculated_at=_NOW)

    assert [p.model_dump() for p in first] == [p.model_dump() for p in second]


def test_projection_does_not_mutate_input() -> None:
    """Патч применяется к КОПИИ: исходный audit_summary остаётся неизменным."""
    audit = _audit({"faq": "fail", "robots_txt": "pass"})
    snapshot = [dict(entry) for entry in audit]

    fix = Fix(fix_id="f", factor="faq", target_verdict="pass")
    _PROJECTION.project(audit, [fix], calculated_at=_NOW)

    assert audit == snapshot


def test_derive_stub_fixes_targets_non_pass_scored_factors() -> None:
    """Стаб-фиксы предлагаются для скорируемых факторов в warn/fail, в порядке WEIGHTS."""
    audit = _audit({"robots_txt": "pass", "http_status": "warn", "json_ld": "fail", "faq": "pass"})
    fixes = derive_stub_fixes(audit)

    factors = [f.factor for f in fixes]
    assert factors == ["http_status", "json_ld"]  # только warn/fail, порядок WEIGHTS
    assert all(f.target_verdict == "pass" for f in fixes)


def test_fix_on_llms_txt_has_zero_delta() -> None:
    """Инвариант §6.5: фикс на llms.txt (вне WEIGHTS) не меняет Score → delta 0."""
    audit = _audit({"robots_txt": "pass", "faq": "pass"})
    fix = Fix(fix_id="fix_llms", factor="llms_txt", target_verdict="pass")

    [projection] = _PROJECTION.project(audit, [fix], calculated_at=_NOW)

    assert projection.delta_score == 0.0
