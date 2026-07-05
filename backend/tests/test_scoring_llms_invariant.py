"""Unit: критический инвариант §6.5 — llms.txt НЕ входит в Score (AC-2).

Три линзы: (a) `llms_txt`/EXCLUDED_FROM_SCORE никогда не среди компонентов; (b) добавление
llms.txt-сигнала во вход НЕ меняет Score; (c) сильные FAQ/schema без llms.txt ≥ сильный
llms.txt при слабых FAQ/schema. Тест форсирует инвариант автоматически (charter §6.5, FR-1.3).
"""

from __future__ import annotations

import datetime

from wizor.scoring.engine import ScoringEngine
from wizor.scoring.weights import EXCLUDED_FROM_SCORE

_NOW = datetime.datetime(2026, 7, 5, 12, 0, tzinfo=datetime.UTC)
_ENGINE = ScoringEngine()


def _audit(verdict_by_factor: dict[str, str]) -> list[dict[str, object]]:
    return [
        {"factor": factor, "verdict": verdict, "detail": "", "data": {}}
        for factor, verdict in verdict_by_factor.items()
    ]


def _score(audit: list[dict[str, object]]) -> float:
    return _ENGINE.score_audit(audit, calculated_at=_NOW).score


def test_llms_txt_never_a_component() -> None:
    """AC-2(a): ни один компонент не входит в EXCLUDED_FROM_SCORE; 'llms_txt' отсутствует."""
    # Даже если краул прислал llms_txt-сигнал — движок его не раскрывает как компонент.
    audit = _audit({"robots_txt": "pass", "faq": "pass", "llms_txt": "pass"})
    names = {c.name for c in _ENGINE.score_audit(audit, calculated_at=_NOW).components}

    assert "llms_txt" not in names
    for excluded in EXCLUDED_FROM_SCORE:
        assert excluded not in names


def test_adding_llms_txt_signal_does_not_change_score() -> None:
    """AC-2(b): два входа, различающихся лишь llms.txt-сигналом, дают ИДЕНТИЧНЫЙ Score."""
    base = _audit({"robots_txt": "pass", "json_ld": "warn", "faq": "fail"})
    with_llms = [*base, {"factor": "llms_txt", "verdict": "pass", "detail": "", "data": {}}]

    base_result = _ENGINE.score_audit(base, calculated_at=_NOW)
    with_llms_result = _ENGINE.score_audit(with_llms, calculated_at=_NOW)

    # llms.txt не может поднять Score — ни через значение, ни через набор компонентов.
    assert base_result.score == with_llms_result.score
    assert base_result.model_dump()["components"] == with_llms_result.model_dump()["components"]


def test_great_faq_schema_beats_great_llms_txt() -> None:
    """AC-2(c): сильные FAQ/schema без llms.txt ≥ сильный llms.txt при слабых FAQ/schema."""
    # Сайт A: отличные реальные левера (schema/FAQ pass), llms.txt отсутствует.
    site_a = _audit(
        {
            "robots_txt": "pass",
            "http_status": "pass",
            "sitemap": "pass",
            "json_ld": "pass",
            "faq": "pass",
            "html_semantics": "pass",
        }
    )
    # Сайт B: отличный llms.txt (не весит), но слабые FAQ/schema/semantics.
    site_b = _audit(
        {
            "robots_txt": "pass",
            "http_status": "pass",
            "sitemap": "pass",
            "json_ld": "fail",
            "faq": "fail",
            "html_semantics": "fail",
            "llms_txt": "pass",
        }
    )

    assert _score(site_a) >= _score(site_b)
    # И строго: llms.txt не спасает B от провала реальных леверов.
    assert _score(site_a) > _score(site_b)
