"""Unit: `ProbeRunner` — N≥5 (AC-3), §6.4 dual-geo диспатч (AC-2), fault-isolation (AC-6),
эвристика mention/citation.

Вся сеть замокана (`httpx.MockTransport` через инъектируемую ``client_factory``) — ни одного
реального probe. Реальный probe требует фондированных ключей + зарубежной ноды egress →
это `deferred_live_gold`, здесь НЕ фейкается.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from wizor.llm_router.config import LLMRouterSettings
from wizor.probe.config import ProbeSettings
from wizor.probe.runner import ProbeRunner, detect_mention_citation
from wizor.probe.schemas import Egress

_FIXED = datetime(2026, 7, 5, 12, 0, 0, tzinfo=UTC)


def _llm(**overrides: str) -> LLMRouterSettings:
    base: dict[str, str] = {
        "openai_api_key": "k",
        "perplexity_api_key": "k",
        "gigachat_api_key": "k",
    }
    base.update(overrides)
    return LLMRouterSettings(_env_file=None, **base)


def _openai_client(content: str = "ответ", status: int = 200) -> httpx.AsyncClient:
    """httpx-клиент с MockTransport, отдающий OpenAI-совместимый ответ (или ошибочный статус)."""

    def handler(request: httpx.Request) -> httpx.Response:
        del request
        if status != 200:
            return httpx.Response(status)
        return httpx.Response(
            200, json={"choices": [{"message": {"content": content}}], "usage": {}}
        )

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class _RecordingFactory:
    """Фабрика клиентов, фиксирующая (egress, proxy) каждого диспатча — для §6.4-проверок."""

    def __init__(self, content: str = "ответ", status: int = 200) -> None:
        self._content = content
        self._status = status
        self.calls: list[tuple[Egress, str | None]] = []

    def __call__(self, egress: Egress, proxy: str | None) -> httpx.AsyncClient:
        self.calls.append((egress, proxy))
        return _openai_client(self._content, self._status)


# --- AC-3: N≥5 прогонов, sequential run_index, инъектированные часы ---------------------


async def test_run_prompt_floors_to_five_runs() -> None:
    factory = _RecordingFactory(content="Acme")
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None, probe_proxy_foreign="http://fp:8080"),
        llm_settings=_llm(),
        client_factory=factory,
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "кто лидер?", "chatgpt", n_runs=3, brand_terms=["Acme"])

    assert len(runs) == 5  # §6.7: пол N≥5 даже при n_runs=3
    assert [r.run_index for r in runs] == [0, 1, 2, 3, 4]
    assert all(r.run_at == _FIXED for r in runs)  # часы инъектированы, не datetime.now
    assert all(r.error is None for r in runs)


# --- AC-2: иностранная модель диспатчится ТОЛЬКО через зарубежный прокси, egress=foreign -


async def test_foreign_model_dispatched_only_via_foreign_proxy() -> None:
    factory = _RecordingFactory(content="ответ")
    runner = ProbeRunner(
        settings=ProbeSettings(
            _env_file=None,
            probe_proxy_foreign="http://fp1:8080",
            probe_proxy_pool="http://fp2:8080",
        ),
        llm_settings=_llm(),
        client_factory=factory,
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "x", "perplexity", brand_terms=["Acme"])

    assert len(factory.calls) == 5
    # §6.4: КАЖДЫЙ диспатч иностранной модели — foreign egress + непустой прокси; НИ ОДНОГО ru.
    assert all(egress == "foreign" for egress, _ in factory.calls)
    assert all(proxy for _, proxy in factory.calls)
    assert all(r.egress == "foreign" for r in runs)
    # Ротация пула задействовала оба прокси.
    assert {proxy for _, proxy in factory.calls} == {"http://fp1:8080", "http://fp2:8080"}


async def test_foreign_model_without_proxy_is_refused_never_dispatched() -> None:
    """AC-2 сердце: нет зарубежного прокси ⇒ probe к ChatGPT НЕ уходит (и не деградирует до ru)."""
    factory = _RecordingFactory()
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None),  # пустой пул прокси
        llm_settings=_llm(),
        client_factory=factory,
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "x", "chatgpt", brand_terms=["Acme"])

    assert factory.calls == []  # НИ ОДНОГО диспатча → РФ-IP к ChatGPT конструктивно невозможен
    assert len(runs) == 5
    assert all(r.error is not None and "probe_geo" in r.error for r in runs)
    assert all(r.egress == "foreign" for r in runs)  # никогда не подменяется на ru
    assert all(r.raw_response == "" and not r.mentioned and not r.cited for r in runs)


async def test_ru_model_dispatched_directly_without_proxy() -> None:
    factory = _RecordingFactory(content="Acme лидер")
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None),
        llm_settings=_llm(),
        client_factory=factory,
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "x", "gigachat", brand_terms=["Acme"])

    assert all(egress == "ru" and proxy is None for egress, proxy in factory.calls)
    assert all(r.egress == "ru" and r.error is None for r in runs)


# --- AC-6: fault isolation — 100% сбойный провайдер даёт error-прогоны, не крах ----------


async def test_fault_isolation_persistent_5xx_yields_error_runs() -> None:
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None, probe_proxy_foreign="http://fp:8080"),
        llm_settings=_llm(),
        client_factory=lambda _e, _p: _openai_client(status=500),
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "x", "chatgpt", brand_terms=["Acme"])

    assert len(runs) == 5  # батч не рухнул
    assert all(r.error is not None and "provider" in r.error for r in runs)
    assert all(r.raw_response == "" and not r.mentioned for r in runs)


async def test_fault_isolation_unavailable_provider_yields_error_runs() -> None:
    """Незаконфигурированный ключ (deferred_live_gold) ⇒ error-прогоны, а не крах/сеть."""
    factory = _RecordingFactory()
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None),
        llm_settings=LLMRouterSettings(_env_file=None),  # gigachat_api_key пуст → недоступен
        client_factory=factory,
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "x", "gigachat", brand_terms=["Acme"])

    assert len(runs) == 5
    assert all(r.error is not None for r in runs)
    assert all(r.egress == "ru" for r in runs)


# --- mention/citation: через раннер и чистой функцией ----------------------------------


async def test_runner_detects_mention_and_citation() -> None:
    content = "Лидер рынка — Acme, подробнее на https://acme.ru/about"
    runner = ProbeRunner(
        settings=ProbeSettings(_env_file=None),
        llm_settings=_llm(),
        client_factory=lambda _e, _p: _openai_client(content=content),
        clock=lambda: _FIXED,
    )
    runs = await runner.run_prompt("p1", "кто лидер?", "gigachat", brand_terms=["Acme", "acme.ru"])

    assert all(r.mentioned for r in runs)
    assert all(r.cited for r in runs)  # присутствует домен-терм acme.ru
    assert all(r.raw_response == content for r in runs)


def test_detect_no_terms_or_empty_text() -> None:
    assert detect_mention_citation("любой текст", []) == (False, False)
    assert detect_mention_citation("", ["Acme"]) == (False, False)


def test_detect_mention_without_citation() -> None:
    assert detect_mention_citation("Acme великолепен", ["Acme"]) == (True, False)


def test_detect_citation_via_domain_term() -> None:
    assert detect_mention_citation("см. acme.ru для деталей", ["Acme", "acme.ru"]) == (True, True)


def test_detect_citation_via_url() -> None:
    assert detect_mention_citation("ссылка https://x.com/acme тут", ["acme"]) == (True, True)


def test_detect_is_case_insensitive() -> None:
    assert detect_mention_citation("ACME рулит", ["acme"]) == (True, False)
