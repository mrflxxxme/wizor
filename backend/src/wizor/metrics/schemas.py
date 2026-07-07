"""Pydantic v2 DTO-шов контекста metrics (P5).

Форма ответа `GET /api/v1/sites/{id}/visibility` (AC-4). Метрики детерминированы из
probe-агрегатов; CI отражает полосу шума (§6.2 honest-forecast: диапазон, не гарантия).
"""

from pydantic import BaseModel, Field


class VisibilityComponents(BaseModel):
    """4 компонента Visibility (FR-2.4), каждый [0..1]."""

    coverage: float = Field(ge=0.0, le=1.0)
    """Presence: доля промптов, где клиент упомянут хотя бы в одной модели."""
    sov: float = Field(ge=0.0, le=1.0)
    """Share of Voice: доля упоминаний клиента vs конкуренты (при наличии конкурент-данных)."""
    citation_rate: float = Field(ge=0.0, le=1.0)
    """Доля ответов, где клиент процитирован как источник / дана ссылка."""
    stability: float = Field(ge=0.0, le=1.0)
    """Стабильность между прогонами (1 − нормированная дисперсия); высокая = мало шума (AC-7)."""


class VisibilityMetrics(BaseModel):
    """Композит Visibility + компоненты + полоса шума (AC-4)."""

    visibility_score: float = Field(ge=0.0, le=100.0)
    """Композит [0–100] из 4 компонентов (детерминированные веса)."""
    components: VisibilityComponents
    ci_lower: float = Field(ge=0.0, le=100.0)
    ci_upper: float = Field(ge=0.0, le=100.0)
    n: int = Field(ge=0)
    """Число прогонов в основе агрегата (N≥5 для заявляемого CI, §6.7)."""
    prompt_set_version: int | None = None
    """Версия набора промптов, по которому считался агрегат (AC-5)."""
