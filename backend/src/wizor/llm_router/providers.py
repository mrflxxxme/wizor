"""Провайдер-адаптеры LLM: тонкий HTTP-слой поверх API (без LangChain, NFR-3).

Единый Protocol :class:`LLMProvider` (`async complete(prompt, ...) -> LLMResponse`) и
конкретные httpx-адаптеры: GigaChat, YandexGPT, vLLM (OSS), OpenAI, Perplexity. Каждый
адаптер принимает ``base_url``/``api_key``/``model`` и httpx-клиент через конструктор
(инъекция) — значит юнит-тесты подменяют клиент mock-транспортом, БЕЗ реальной сети (§6.9,
ключи только из config/Lockbox). Транзиентные сбои (таймаут/5xx/сеть) ретраятся tenacity —
3 попытки, экспоненциальный backoff (AC-5); 4xx (клиентская ошибка) НЕ ретрается.

Непровайдерский случай — :class:`UnavailableProvider`: если провайдер не сконфигурирован
(пустой ключ/endpoint), `complete` бросает :class:`ProviderUnavailableError`, а роутер
изолирует это (RU-fallback или явная ошибка, НЕ тихий иностранный fallback).
"""

from __future__ import annotations

from time import perf_counter
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from wizor.llm_router.schemas import LLMResponse, Provider, TaskType

if TYPE_CHECKING:
    from wizor.llm_router.config import LLMRouterSettings

# Параметры ретрая (AC-5). Backoff экспоненциальный; small-множитель — чтобы юнит-тесты
# с mock-транспортом не висели, оставаясь экспоненциальными (prod может поднять через env).
_RETRY_ATTEMPTS = 3
_RETRY_WAIT_MULTIPLIER = 0.05
_RETRY_WAIT_MAX = 1.0
_SERVER_ERROR_FLOOR = 500


class ProviderError(RuntimeError):
    """Базовая ошибка провайдер-адаптера."""


class ProviderUnavailableError(ProviderError):
    """Провайдер не сконфигурирован (нет ключа/endpoint) — вызов невозможен (§6.9)."""


class ProviderCallError(ProviderError):
    """Вызов провайдера не удался (после ретраев транзиентных сбоев)."""


def _is_transient(exc: BaseException) -> bool:
    """Транзиентна ли ошибка (стоит ли ретраить): таймаут/сеть/5xx — да; 4xx — нет."""
    if isinstance(exc, httpx.TimeoutException | httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= _SERVER_ERROR_FLOOR
    return False


@runtime_checkable
class LLMProvider(Protocol):
    """Единый интерфейс провайдера. ``provider`` — метка для LLMResponse/маршрутизации."""

    provider: Provider

    async def complete(
        self, prompt: str, *, task_type: TaskType = "content_gen", **kwargs: Any
    ) -> LLMResponse: ...


class UnavailableProvider:
    """Заглушка несконфигурированного провайдера: любой вызов → ошибка (не сеть).

    Аналог no-op PostHog (P1) / stub-адаптеров (P2): пустой ключ ⇒ провайдер «выключен».
    Роутер ловит ошибку и изолирует (fallback по RU-цепочке или явный no-provider).
    """

    def __init__(self, provider: Provider, *, reason: str = "не сконфигурирован") -> None:
        self.provider = provider
        self._reason = reason

    async def complete(
        self, prompt: str, *, task_type: TaskType = "content_gen", **kwargs: Any
    ) -> LLMResponse:
        del prompt, task_type, kwargs  # заглушка: вход не используется
        msg = f"провайдер {self.provider!r} недоступен: {self._reason} (§6.9)"
        raise ProviderUnavailableError(msg)


class _HttpProvider:
    """База httpx-адаптера: инъекция клиента, ретрай, тайминг, разбор ответа.

    Подклассы задают ``provider`` и переопределяют ``_endpoint``/`_headers`/`_payload`/
    `_parse` под конкретный API. Клиент инъектируется (тесты дают mock-транспорт); если
    не передан — создаётся собственный (владение → закрывается в `aclose`).
    """

    provider: Provider

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        client: httpx.AsyncClient | None = None,
        timeout_s: float = 30.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout_s)

    async def aclose(self) -> None:
        """Закрыть собственный httpx-клиент (инъектированный — не наш, не трогаем)."""
        if self._owns_client:
            await self._client.aclose()

    # --- Точки расширения под конкретный API (переопределяются подклассом) ---
    def _endpoint(self) -> str:
        return f"{self._base_url}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    def _payload(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        return payload

    def _parse(self, data: dict[str, Any], task_type: TaskType, latency_ms: float) -> LLMResponse:
        """Разобрать OpenAI-совместимый ответ (chat.completions) → LLMResponse."""
        choices = data.get("choices") or [{}]
        text = str(choices[0].get("message", {}).get("content", ""))
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            provider=self.provider,
            task_type=task_type,
            model=str(data.get("model", self._model)),
            tokens_prompt=int(usage.get("prompt_tokens", 0)),
            tokens_completion=int(usage.get("completion_tokens", 0)),
            latency_ms=latency_ms,
        )

    async def complete(
        self, prompt: str, *, task_type: TaskType = "content_gen", **kwargs: Any
    ) -> LLMResponse:
        """Выполнить вызов с ретраем транзиентных сбоев (AC-5).

        Ретраи исчерпаны (транзиентный сбой не прошёл) ИЛИ не-транзиентный сбой (4xx) →
        raw `httpx.HTTPError` конвертируется в доменную `ProviderCallError`. Иначе фасад
        `LLMRouter.probe/complete` (ловит `except ProviderError`) НЕ изолировал бы сбой —
        одно persistent-падение уронило бы весь probe-батч (AC-5).
        """
        try:
            return await self._complete_with_retry(prompt, task_type=task_type, **kwargs)
        except httpx.HTTPError as exc:
            raise ProviderCallError(f"{self.provider}: {exc!r}") from exc

    @retry(
        stop=stop_after_attempt(_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=_RETRY_WAIT_MULTIPLIER, max=_RETRY_WAIT_MAX),
        retry=retry_if_exception(_is_transient),
        reraise=True,
    )
    async def _complete_with_retry(
        self, prompt: str, *, task_type: TaskType, **kwargs: Any
    ) -> LLMResponse:
        started = perf_counter()
        response = await self._client.post(
            self._endpoint(), json=self._payload(prompt, **kwargs), headers=self._headers()
        )
        response.raise_for_status()  # 4xx/5xx → HTTPStatusError (5xx ретрается, 4xx — нет)
        latency_ms = (perf_counter() - started) * 1000.0
        return self._parse(response.json(), task_type, latency_ms)


class GigaChatProvider(_HttpProvider):
    """GigaChat (Sber) — OpenAI-совместимый chat.completions. RU-default (§6.6)."""

    provider: Provider = "gigachat"


class VLLMProvider(_HttpProvider):
    """vLLM (OSS self-hosted, Qwen/Saiga) — OpenAI-совместимый API. Batch-cost, без ПД."""

    provider: Provider = "vllm"

    def _headers(self) -> dict[str, str]:
        # vLLM ключ опционален (self-hosted нода); Authorization только если задан.
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers


class OpenAIProvider(_HttpProvider):
    """OpenAI — OpenAI-совместимый chat.completions. Иностранный, opt-in / probe-канал."""

    provider: Provider = "openai"


class PerplexityProvider(_HttpProvider):
    """Perplexity — OpenAI-совместимый chat.completions. Иностранный, probe-канал."""

    provider: Provider = "perplexity"


class YandexGPTProvider(_HttpProvider):
    """YandexGPT (Yandex Cloud Foundation Models) — собственный формат completion. RU-default.

    API отличается от OpenAI: endpoint ``/completion``, ключ через ``Api-Key``, тело с
    ``modelUri``/``completionOptions``/``messages`` (role+text), ответ в ``result.alternatives``.
    """

    provider: Provider = "yandexgpt"

    def __init__(self, *, folder_id: str = "", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._folder_id = folder_id

    def _endpoint(self) -> str:
        return f"{self._base_url}/completion"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Api-Key {self._api_key}", "Content-Type": "application/json"}

    def _model_uri(self) -> str:
        # gpt://<folder_id>/<model>/latest — Yandex FM формат идентификатора модели.
        return f"gpt://{self._folder_id}/{self._model}/latest"

    def _payload(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        return {
            "modelUri": self._model_uri(),
            "completionOptions": {
                "temperature": kwargs.get("temperature", 0.3),
                "maxTokens": kwargs.get("max_tokens", 2000),
            },
            "messages": [{"role": "user", "text": prompt}],
        }

    def _parse(self, data: dict[str, Any], task_type: TaskType, latency_ms: float) -> LLMResponse:
        result = data.get("result") or {}
        alternatives = result.get("alternatives") or [{}]
        text = str(alternatives[0].get("message", {}).get("text", ""))
        usage = result.get("usage") or {}
        return LLMResponse(
            text=text,
            provider=self.provider,
            task_type=task_type,
            model=str(result.get("modelVersion", self._model)),
            tokens_prompt=int(usage.get("inputTextTokens", 0)),
            tokens_completion=int(usage.get("completionTokens", 0)),
            latency_ms=latency_ms,
        )


# Фабрики конкретных адаптеров (OpenAI-совместимые получают одинаковый набор аргументов).
_OPENAI_COMPATIBLE: dict[Provider, type[_HttpProvider]] = {
    "gigachat": GigaChatProvider,
    "vllm": VLLMProvider,
    "openai": OpenAIProvider,
    "perplexity": PerplexityProvider,
}


def make_provider(
    provider: Provider,
    settings: LLMRouterSettings,
    *,
    client: httpx.AsyncClient | None = None,
) -> LLMProvider:
    """Собрать адаптер провайдера из настроек (или Unavailable, если не сконфигурирован).

    Единая точка инъекции кредов из config → адаптер (ключи не хардкодятся, §6.9). Не
    сконфигурированный провайдер → :class:`UnavailableProvider` (роутер изолирует). Для
    anthropic/gemini полноценный адаптер в P4 не реализован — они opt-in и не в дефолтных
    маршрутах; возвращается Unavailable с явной причиной (расширяется JIT в следующих фазах).
    """
    if not settings.is_configured(provider):
        return UnavailableProvider(provider)

    common: dict[str, Any] = {
        "base_url": settings.base_url(provider),
        "api_key": settings.api_key(provider),
        "model": settings.model_name(provider),
        "client": client,
        "timeout_s": settings.llm_http_timeout_s,
    }

    if provider == "yandexgpt":
        return YandexGPTProvider(folder_id=settings.yandexgpt_folder_id, **common)

    adapter_cls = _OPENAI_COMPATIBLE.get(provider)
    if adapter_cls is None:
        return UnavailableProvider(provider, reason="адаптер не реализован в P4 (opt-in, JIT)")
    return adapter_cls(**common)
