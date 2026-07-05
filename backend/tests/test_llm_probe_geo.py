"""Unit: probe dual-geo (AC-4, §6.4/NFR-2) — probe к ChatGPT/Perplexity только через
зарубежную ноду; РФ-IP к иностранной модели структурно отвергается.

Проверяется правило маршрутизации (роутер предоставляет geo-rule; probe-контекст P5 его
исполняет по факту). Ни одного реального вызова.
"""

from __future__ import annotations

from typing import Any

import pytest

from wizor.llm_router.config import LLMRouterSettings
from wizor.llm_router.router import LLMRouter
from wizor.llm_router.routing import (
    FOREIGN_PROVIDERS,
    ProbeGeoViolationError,
    RouteDecision,
    assert_geo,
    egress_for,
    resolve_route,
)
from wizor.llm_router.schemas import LLMRequest, LLMResponse, Provider


class _FakeProvider:
    def __init__(self, provider: Provider) -> None:
        self.provider = provider

    async def complete(
        self, prompt: str, *, task_type: Any = "probe", **kwargs: Any
    ) -> LLMResponse:
        del prompt, kwargs
        return LLMResponse(text="cited", provider=self.provider, task_type=task_type, model="fake")


def _settings(**overrides: Any) -> LLMRouterSettings:
    base: dict[str, Any] = {
        "openai_api_key": "k",
        "perplexity_api_key": "k",
        "gigachat_api_key": "k",
    }
    base.update(overrides)
    return LLMRouterSettings(_env_file=None, **base)


# --- Правило egress: инопровайдер ⇒ foreign, RU/OSS ⇒ ru -------------------------------


def test_egress_foreign_for_foreign_providers() -> None:
    foreign: tuple[Provider, ...] = ("openai", "anthropic", "perplexity", "gemini")
    for provider in foreign:
        assert egress_for(provider) == "foreign"


def test_egress_ru_for_ru_and_oss_providers() -> None:
    ru_oss: tuple[Provider, ...] = ("gigachat", "yandexgpt", "vllm")
    for provider in ru_oss:
        assert egress_for(provider) == "ru"


# --- AC-4: probe по умолчанию → иностранный провайдер + зарубежный egress --------------


def test_probe_default_routes_to_foreign_with_foreign_egress() -> None:
    decision = resolve_route(LLMRequest(prompt="кто лидер рынка?", task_type="probe"))
    assert decision.provider in FOREIGN_PROVIDERS
    assert decision.egress == "foreign"
    assert decision.contains_pd is False


def test_probe_override_to_perplexity_stays_foreign() -> None:
    decision = resolve_route(
        LLMRequest(prompt="x", task_type="probe", provider_override="perplexity")
    )
    assert decision.provider == "perplexity"
    assert decision.egress == "foreign"


# --- Структурный предохранитель: РФ-egress к иностранной модели отвергается -----------


def test_assert_geo_rejects_ru_egress_to_foreign_provider() -> None:
    """Сконструированное «РФ-IP к ChatGPT» решение обязано быть отвергнуто (§6.4/NFR-2)."""
    bad = RouteDecision(provider="openai", egress="ru", contains_pd=False, reason="handcrafted")
    with pytest.raises(ProbeGeoViolationError):
        assert_geo(bad)


def test_assert_geo_accepts_resolved_probe_decision() -> None:
    decision = resolve_route(LLMRequest(prompt="x", task_type="probe"))
    assert_geo(decision)  # не должно бросить


def test_probe_to_ru_model_uses_ru_egress_legitimately() -> None:
    """Probe к RU-модели (GigaChat) легитимно идёт с РФ-egress (§6.4 бьёт лишь ин-модели)."""
    decision = resolve_route(
        LLMRequest(prompt="x", task_type="probe", provider_override="gigachat")
    )
    assert decision.provider == "gigachat"
    assert decision.egress == "ru"
    assert_geo(decision)  # RU-провайдер с ru-egress — валиден


# --- Config-уровень: probe_egress_region="ru" валит конфиг ------------------------------


def test_config_rejects_ru_probe_egress() -> None:
    settings = _settings(probe_egress_region="ru")
    assert settings.probe_egress_is_foreign() is False
    with pytest.raises(ValueError, match=r"§6\.4"):
        settings.assert_probe_egress_foreign()


def test_config_default_probe_egress_is_foreign() -> None:
    assert _settings().probe_egress_is_foreign() is True


# --- Роутер: probe-путь не делает RU-предположения для ChatGPT --------------------------


@pytest.mark.asyncio
async def test_router_probe_uses_foreign_provider() -> None:
    requested: list[Provider] = []

    def factory(provider: Provider) -> _FakeProvider:
        requested.append(provider)
        return _FakeProvider(provider)

    router = LLMRouter(settings=_settings(), provider_factory=factory)
    result = await router.probe(LLMRequest(prompt="x", task_type="probe", n_runs=5))
    assert requested and all(p in FOREIGN_PROVIDERS for p in requested)
    assert len(result.responses) == 5
    # Ни один RU-провайдер не был использован как probe-канал к иностранной модели.
    assert "gigachat" not in requested
    assert "yandexgpt" not in requested
