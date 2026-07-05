"""Pydantic v2 DTO-шов контекста llm-router (P4).

Единая граница типов между `LLMRouter`/провайдер-адаптерами (домен) и persistence/
config/API. Меняешь форму — согласованно (charter §7 контракт). Провайдеры и категории
провайдеров — константы здесь, чтобы routing-таблица и compliance-проверки (§6.6) ссылались
на один источник.
"""

from typing import Literal

from pydantic import BaseModel, Field

TaskType = Literal["content_gen", "probe", "batch", "schema_gen"]
"""Тип задачи → правило маршрутизации. content_gen — ПД клиента (RU-default, §6.6)."""

Provider = Literal["gigachat", "yandexgpt", "vllm", "openai", "anthropic", "perplexity", "gemini"]

RU_PROVIDERS: tuple[Provider, ...] = ("gigachat", "yandexgpt")
"""RU-резидентные провайдеры — дефолт для content_gen с ПД клиента (§6.6)."""
OSS_PROVIDERS: tuple[Provider, ...] = ("vllm",)
"""Self-hosted OSS (Qwen/Saiga via vLLM) — batch-cost, без ПД клиента."""
FOREIGN_PROVIDERS: tuple[Provider, ...] = ("openai", "anthropic", "perplexity", "gemini")
"""Иностранные — opt-in для не-ПД задач; probe-канал только через зарубежные ноды (§6.4/NFR-2)."""


class LLMRequest(BaseModel):
    """Запрос к роутеру. Роутер сам выбирает провайдера по task_type + tenant-override."""

    prompt: str
    task_type: TaskType
    tenant_id: str | None = None
    provider_override: Provider | None = None
    """Opt-in: тенант явно выбрал провайдера (напр. иностранный).
    НЕ применяется для ПД-задач, если ломает §6.6 (тогда downgrade к RU-дефолту)."""
    n_runs: int = Field(default=1, ge=1)
    """Число прогонов (probe-канал: N≥5 для uncertainty, AC-7)."""


class LLMResponse(BaseModel):
    """Ответ одного вызова провайдера."""

    text: str
    provider: Provider
    task_type: TaskType
    model: str
    tokens_prompt: int = 0
    tokens_completion: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0


class UncertaintyStats(BaseModel):
    """Агрегация неопределённости probe-канала (N≥5 + доверительный интервал, AC-7, §6.7)."""

    mean: float
    ci_lower: float
    ci_upper: float
    n: int = Field(ge=1)


class ProbeResult(BaseModel):
    """Результат probe-канала: N ответов + агрегированная uncertainty."""

    responses: list[LLMResponse] = Field(default_factory=list)
    uncertainty: UncertaintyStats | None = None


class ProviderConfigDTO(BaseModel):
    """Правило маршрутизации/включения провайдера для тенанта (persistence-форма)."""

    tenant_id: str
    task_type: TaskType
    provider: Provider
    enabled: bool = True
