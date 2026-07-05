"""Unit: маршрутизация LLM-роутера — AC-1 (content_gen→RU), AC-2 (opt-in иностранных /
§6.6 отказ на ПД), AC-3 (batch→vLLM), + RU-fallback без тихого иностранного fallback.

Всё на фейках: ни одного реального провайдер-вызова (§6.9). Проверяется КУДА роутер
направляет вызов (структурное enforcement §6.6), а не сеть.
"""

from __future__ import annotations

from typing import Any

import pytest

from wizor.llm_router.config import LLMRouterSettings
from wizor.llm_router.router import LLMRouter, NoAvailableProviderError
from wizor.llm_router.routing import resolve_route
from wizor.llm_router.schemas import LLMRequest, LLMResponse, Provider


class _FakeProvider:
    """Фейк-провайдер: фиксирует вызовы, отдаёт детерминированный ответ (без сети)."""

    def __init__(self, provider: Provider) -> None:
        self.provider = provider
        self.calls = 0

    async def complete(
        self, prompt: str, *, task_type: Any = "content_gen", **kwargs: Any
    ) -> LLMResponse:
        del prompt, kwargs
        self.calls += 1
        return LLMResponse(text="ok", provider=self.provider, task_type=task_type, model="fake")


class _FactorySpy:
    """Фабрика-шпион: запоминает, какого провайдера запросил роутер."""

    def __init__(self) -> None:
        self.requested: list[Provider] = []

    def __call__(self, provider: Provider) -> _FakeProvider:
        self.requested.append(provider)
        return _FakeProvider(provider)


def _settings(**overrides: Any) -> LLMRouterSettings:
    """Настройки со всеми провайдерами сконфигурированными (override → "" отключает)."""
    base: dict[str, Any] = {
        "gigachat_api_key": "k",
        "yandexgpt_api_key": "k",
        "yandexgpt_folder_id": "f",
        "vllm_base_url": "http://vllm:8000/v1",
        "openai_api_key": "k",
        "perplexity_api_key": "k",
        "anthropic_api_key": "k",
        "gemini_api_key": "k",
    }
    base.update(overrides)
    return LLMRouterSettings(_env_file=None, **base)


def _router(settings: LLMRouterSettings, spy: _FactorySpy) -> LLMRouter:
    return LLMRouter(settings=settings, provider_factory=spy)


# --- AC-1: content_gen без override → RU-провайдер (GigaChat) --------------------------


async def test_content_gen_defaults_to_ru_gigachat() -> None:
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(LLMRequest(prompt="сгенерируй FAQ", task_type="content_gen"))
    assert resp.provider == "gigachat"
    assert spy.requested == ["gigachat"]


async def test_schema_gen_defaults_to_ru() -> None:
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(LLMRequest(prompt="schema.org", task_type="schema_gen"))
    assert resp.provider == "gigachat"
    assert spy.requested == ["gigachat"]


# --- AC-2: opt-in иностранных + §6.6 отказ иностранного на ПД-задаче -------------------


async def test_foreign_optin_on_non_pd_batch_honored() -> None:
    """Не-ПД задача (batch) с override=openai → вызов ИДЁТ в OpenAI (opt-in работает)."""
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(
        LLMRequest(prompt="батч", task_type="batch", provider_override="openai")
    )
    assert resp.provider == "openai"
    assert spy.requested == ["openai"]


async def test_foreign_override_on_content_gen_pd_refused_and_downgraded() -> None:
    """§6.6: override=openai на content_gen (ПД) → ОТКАЗ, downgrade на RU; OpenAI не зовётся."""
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(
        LLMRequest(prompt="текст клиента", task_type="content_gen", provider_override="openai")
    )
    assert resp.provider == "gigachat"
    assert "openai" not in spy.requested


def test_resolve_route_marks_refused_foreign_override_on_pd() -> None:
    """Структурный след §6.6: отказанный иностранный override зафиксирован в решении."""
    decision = resolve_route(
        LLMRequest(prompt="x", task_type="content_gen", provider_override="anthropic")
    )
    assert decision.provider == "gigachat"
    assert decision.refused_override == "anthropic"
    assert decision.reason == "foreign_override_refused_pd"
    assert decision.egress == "ru"
    assert decision.contains_pd is True


async def test_content_gen_never_calls_foreign_without_override() -> None:
    """content_gen без override НИКОГДА не зовёт иностранного (AC-2, вторая половина)."""
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    await router.complete(LLMRequest(prompt="x", task_type="content_gen"))
    assert all(p not in ("openai", "anthropic", "perplexity", "gemini") for p in spy.requested)


async def test_ru_override_on_content_gen_honored() -> None:
    """RU-override (yandexgpt) на ПД-задаче допустим — это не иностранный провайдер."""
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(
        LLMRequest(prompt="x", task_type="content_gen", provider_override="yandexgpt")
    )
    assert resp.provider == "yandexgpt"
    assert spy.requested == ["yandexgpt"]


# --- AC-3: batch → vLLM (OSS self-hosted) ---------------------------------------------


async def test_batch_defaults_to_vllm() -> None:
    spy = _FactorySpy()
    router = _router(_settings(), spy)
    resp = await router.complete(LLMRequest(prompt="батч", task_type="batch"))
    assert resp.provider == "vllm"
    assert spy.requested == ["vllm"]


# --- RU-fallback без тихого иностранного fallback (§6.6, system-prompt failure mode) ---


async def test_ru_fallback_to_yandex_when_gigachat_unavailable() -> None:
    """GigaChat не сконфигурирован → RU-fallback на YandexGPT (не на иностранного)."""
    spy = _FactorySpy()
    router = _router(_settings(gigachat_api_key=""), spy)
    resp = await router.complete(LLMRequest(prompt="x", task_type="content_gen"))
    assert resp.provider == "yandexgpt"
    assert spy.requested == ["yandexgpt"]


async def test_no_silent_foreign_fallback_when_all_ru_down() -> None:
    """Все RU-провайдеры недоступны на ПД-задаче → явная ошибка, НЕ иностранный fallback."""
    spy = _FactorySpy()
    # openai сконфигурирован, но НЕ должен быть подхвачен для content_gen (ПД).
    router = _router(_settings(gigachat_api_key="", yandexgpt_api_key=""), spy)
    with pytest.raises(NoAvailableProviderError):
        await router.complete(LLMRequest(prompt="x", task_type="content_gen"))
    assert spy.requested == []  # ни один иностранный не запрошен
