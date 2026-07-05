"""Pydantic v2 DTO-шов контекста scoring (P3).

Граница типов между `ScoringEngine`/`ProjectionEngine` (домен) и persistence/API.
Форма стабильна и не зависит от конкретных весов (`weights.py`) — движок наполняет
её. Потребитель: `recommendations` (P6). Инвариант §6.5: llms.txt не среди компонентов.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["pass", "warn", "fail", "deferred"]


class ScoreComponent(BaseModel):
    """Один раскрытый компонент Score (AC-3) — прозрачность для пользователя."""

    name: str
    """Идентификатор фактора (совпадает с crawler FactorVerdict.factor)."""
    layer: Literal["discovery", "comprehension"]
    weight: float
    """Вес фактора в Score (доля/пункты по нормировке weights.py)."""
    value: float
    """Нормированное значение фактора [0..1] (из verdict + data)."""
    verdict: Verdict
    contribution: float
    """Фактический вклад в итог = weight * value (пункты Score)."""
    description: str
    """RU-пояснение: почему это citation-рычаг и что означает вердикт."""


class ScoreProjection(BaseModel):
    """Детерминированная Readiness-проекция для одного фикса (AC-4)."""

    fix_id: str
    delta_score: float
    """Прирост Score при применении фикса (пересчёт без краула)."""
    new_score: float
    description: str = ""


class ScoreResult(BaseModel):
    """Итог расчёта AI-Readiness Score — детерминированный, версионированный."""

    site_url: str
    score: float = Field(ge=0.0, le=100.0)
    score_version: str
    """Версия набора весов (weights.SCORE_VERSION) — смена формулы = новая версия."""
    components: list[ScoreComponent] = Field(default_factory=list)
    projection: list[ScoreProjection] = Field(default_factory=list)
    calculated_at: datetime
