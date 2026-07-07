"""Pydantic v2 DTO-шов контекста probe (P5).

Граница типов между probe-раннером (домен, dual-geo) и persistence/Celery/метриками.
Модели probe и их гео-класс — константы здесь (единый источник для §6.4-проверок).
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ModelId = Literal["alice_yandex", "gigachat", "chatgpt", "perplexity"]
"""4 probe-модели MVP (FR-2.2)."""

RU_MODELS: tuple[ModelId, ...] = ("alice_yandex", "gigachat")
"""RU-резидентные модели → RU-ноды (Yandex Cloud FM / GigaChat API)."""
FOREIGN_MODELS: tuple[ModelId, ...] = ("chatgpt", "perplexity")
"""Иностранные модели → ТОЛЬКО зарубежные ноды + прокси, НИКОГДА РФ-IP (§6.4, AC-2)."""

Egress = Literal["ru", "foreign"]
"""Гео-класс исходящего запроса. Для FOREIGN_MODELS обязан быть 'foreign' (§6.4)."""


class ProbeRun(BaseModel):
    """Один сырой прогон одного промпта на одной модели (N≥5 таких на промпт×модель, FR-2.3)."""

    prompt_id: str
    model: ModelId
    run_index: int = Field(ge=0)
    raw_response: str
    mentioned: bool
    """Бренд/сайт клиента упомянут в ответе (→ Coverage/Presence)."""
    cited: bool
    """Клиент процитирован как источник / дана ссылка (→ Citation Rate)."""
    egress: Egress
    """Гео-класс фактического запроса — для §6.4 audit (foreign-модель обязана быть 'foreign')."""
    run_at: datetime
    error: str | None = None
    """Установлено, если прогон упал (fault-isolation: не роняет батч, AC-6)."""


class PromptSetDTO(BaseModel):
    """Версионируемый набор промптов сайта (FR-2.1, AC-5)."""

    id: str
    site_id: str
    version: int = Field(ge=1)
    prompts: list[str] = Field(default_factory=list)


class PromptModelAggregate(BaseModel):
    """Агрегат N прогонов для одного промпта×модели (вход для метрик)."""

    prompt_id: str
    model: ModelId
    n: int = Field(ge=0)
    n_success: int = Field(ge=0)
    mention_rate: float = 0.0
    citation_rate: float = 0.0
    stability: float = 0.0
    """1 − нормированная дисперсия mention между прогонами (AC-7)."""
