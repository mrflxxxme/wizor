"""Unit: retry + fault-isolation (AC-5).

Retry — на РЕАЛЬНОМ адаптере с mock httpx-транспортом (без сети): транзиентные (5xx/таймаут)
ретраятся, 4xx — нет. Fault-isolation — на probe-пути роутера: провал одного прогона не
роняет остальные.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from wizor.llm_router.config import LLMRouterSettings
from wizor.llm_router.providers import ProviderCallError, make_provider
from wizor.llm_router.router import LLMRouter
from wizor.llm_router.schemas import LLMRequest, LLMResponse, Provider

_OK_PAYLOAD: dict[str, Any] = {
    "model": "m",
    "choices": [{"message": {"content": "привет"}}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2},
}


def _client(handler: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://mock")


def _settings() -> LLMRouterSettings:
    return LLMRouterSettings(_env_file=None, openai_api_key="k")


# --- AC-5: транзиентные (5xx) ретраятся до успеха --------------------------------------


async def test_retry_on_5xx_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=_OK_PAYLOAD)

    provider = make_provider("openai", _settings(), client=_client(handler))
    resp = await provider.complete("hi", task_type="probe")
    assert resp.text == "привет"
    assert calls["n"] == 3


async def test_retry_on_timeout_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ReadTimeout("timeout", request=request)
        return httpx.Response(200, json=_OK_PAYLOAD)

    provider = make_provider("openai", _settings(), client=_client(handler))
    resp = await provider.complete("hi", task_type="probe")
    assert resp.text == "привет"
    assert calls["n"] == 3


# --- AC-5: 4xx НЕ ретраится (клиентская ошибка) ----------------------------------------


async def test_no_retry_on_4xx() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        calls["n"] += 1
        return httpx.Response(400, json={"error": "bad request"})

    provider = make_provider("openai", _settings(), client=_client(handler))
    with pytest.raises(ProviderCallError):  # 4xx → доменная ошибка (не raw httpx), AC-5
        await provider.complete("hi", task_type="probe")
    assert calls["n"] == 1  # 4xx не ретраится


async def test_exhausted_retries_reraise() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        calls["n"] += 1
        return httpx.Response(500)

    provider = make_provider("openai", _settings(), client=_client(handler))
    with pytest.raises(ProviderCallError):  # ретраи исчерпаны → доменная ошибка (AC-5)
        await provider.complete("hi", task_type="probe")
    assert calls["n"] == 3


# --- AC-5: fault-isolation на probe-пути роутера ---------------------------------------


class _FlakyProvider:
    """Фейк-провайдер: падает на заданных индексах прогонов, иначе успех."""

    def __init__(self, provider: Provider, *, fail_on: set[int]) -> None:
        self.provider = provider
        self._fail_on = fail_on
        self.calls = 0

    async def complete(
        self, prompt: str, *, task_type: Any = "probe", **kwargs: Any
    ) -> LLMResponse:
        del prompt, kwargs
        idx = self.calls
        self.calls += 1
        if idx in self._fail_on:
            msg = f"провайдер упал на прогоне {idx}"
            raise ProviderCallError(msg)
        return LLMResponse(text="ok", provider=self.provider, task_type=task_type, model="fake")


async def test_probe_fault_isolation_one_failure_does_not_crash_batch() -> None:
    flaky = _FlakyProvider("openai", fail_on={1, 3})  # прогоны 1 и 3 падают
    router = LLMRouter(
        settings=_settings(),
        provider_factory=lambda _p: flaky,
    )
    result = await router.probe(LLMRequest(prompt="x", task_type="probe", n_runs=5))
    # Все 5 прогонов ПОПЫТАНЫ, 2 упали, 3 успешных собраны — батч не рухнул.
    assert flaky.calls == 5
    assert len(result.responses) == 3
    # Недостаточно успешных (<5) для честного CI → uncertainty не заявляется.
    assert result.uncertainty is None


async def test_probe_fault_isolation_real_adapter_persistent_5xx() -> None:
    """Fault-isolation на РЕАЛЬНОМ адаптере (не фейке): persistent 5xx через httpx.MockTransport.

    Регрессия ревью P4: раньше `complete()` пробрасывал raw `httpx.HTTPError`, который probe
    (`except ProviderError`) НЕ ловил → один persistent-сбой ронял весь батч. Теперь
    httpx→`ProviderCallError`, и probe изолирует каждый сбойный прогон (AC-5) через реальный
    exception-путь, а не через фейк, поднимающий уже-доменную ошибку.
    """
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        calls["n"] += 1
        return httpx.Response(500)

    settings = _settings()
    router = LLMRouter(
        settings=settings,
        provider_factory=lambda _p: make_provider("openai", settings, client=_client(handler)),
    )
    # Батч НЕ падает несмотря на raw-httpx сбои на всех прогонах (real-path isolation).
    result = await router.probe(LLMRequest(prompt="x", task_type="probe", n_runs=5))
    assert result.responses == []  # все 5 упали, но raw httpx не пролез — батч жив
    assert result.uncertainty is None  # 0 успешных → CI не заявляется (§6.2/§6.7)
    assert calls["n"] >= 5  # каждый из 5 прогонов реально дошёл до адаптера
