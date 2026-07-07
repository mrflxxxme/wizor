"""``ProbeRunner`` — исполняемый слой dual-geo probe-мониторинга (P5, read-only).

На вход — один промпт × одна модель; на выход — N≥5 сырых прогонов (:class:`ProbeRun`,
FR-2.3/AC-3). Каждый прогон:

* берёт egress ИЗ модели (`geo.egress_for_model`) — вызывающий его не задаёт;
* для иностранной модели берёт зарубежный прокси из пула (ротация) и строит httpx-клиент
  через него; для RU-модели — прямой клиент;
* проходит `geo.assert_probe_geo` ПЕРЕД диспатчем (священный §6.4/NFR-2 предохранитель,
  привязанный к фактическому прокси) — иначе диспатч не случается;
* вызывает модель реюзом P4-адаптера (`llm_router.make_provider`, ``task_type="probe"``),
  чей tenacity-ретрай транзиентных сбоев наследуется (mirror P4, AC-5);
* извлекает ``mentioned``/``cited`` чистой эвристикой `detect_mention_citation`.

**Fault isolation (AC-6).** Сбой прогона (недоступный провайдер, 4xx/5xx после ретраев,
таймаут) НЕ роняет батч — фиксируется как :class:`ProbeRun` с ``error``. Нарушение §6.4
(иностранная модель без прокси) тоже отдаётся error-прогоном (диспатч отклонён), а не
тихим РФ-fallback и не крахом.

Часы инъектируются (``clock``); чистая логика (`detect_mention_citation`) времени не трогает.
Клиент/провайдер инъектируется через ``client_factory`` — тесты дают ``httpx.MockTransport``,
реальной сети нет.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import structlog

from wizor.llm_router.config import LLMRouterSettings, get_llm_settings
from wizor.llm_router.providers import ProviderError, make_provider
from wizor.probe.config import ProbeSettings, get_probe_settings
from wizor.probe.geo import (
    ProbeGeoViolationError,
    assert_probe_geo,
    egress_for_model,
    provider_for_model,
)
from wizor.probe.schemas import Egress, ModelId, ProbeRun

logger = structlog.get_logger(__name__)

# Минимум прогонов на промпт×модель (§6.7, FR-2.3, AC-3). Зеркалит llm_router.MIN_RUNS.
MIN_RUNS = 5

# Часы: инъектируемая функция «сейчас» (чистая логика её не зовёт).
Clock = Callable[[], datetime]

# Фабрика httpx-клиента по egress + прокси. Foreign ⇒ клиент через зарубежный прокси,
# ru ⇒ прямой клиент. Инъектируется (тесты дают MockTransport, без сети).
ClientFactory = Callable[[Egress, str | None], httpx.AsyncClient]

# URL в тексте ответа (для сигнала цитирования: ссылка на домен клиента).
_URL_RE = re.compile(r"https?://[^\s)\]>\"']+", re.IGNORECASE)


def detect_mention_citation(text: str, brand_terms: Sequence[str]) -> tuple[bool, bool]:
    """Чистая эвристика: упомянут ли бренд (``mentioned``) и процитирован ли (``cited``).

    ``mentioned`` — любой бренд/домен-терм встречается в ответе (регистронезависимо):
    основа Coverage/Presence (FR-2.4). ``cited`` — терм-домен (содержит ``.``) присутствует
    в тексте ИЛИ бренд-терм встречается внутри URL: основа Citation Rate (дана ссылка /
    процитирован как источник). ``cited`` ⇒ ``mentioned`` (домен/URL-терм входит в общий набор).

    Чистая и детерминированная (без I/O, без времени) — тестируется без сети. Пустой текст
    или пустой набор термов ⇒ ``(False, False)``.
    """
    terms = [t.lower() for t in brand_terms if t.strip()]
    if not text or not terms:
        return (False, False)
    haystack = text.lower()

    mentioned = any(term in haystack for term in terms)
    if not mentioned:
        return (False, False)

    # Цитирование: домен-терм (с точкой) прямо в тексте …
    cited = any("." in term and term in haystack for term in terms)
    if not cited:
        # … либо бренд-терм внутри какого-либо URL (ссылка на источник).
        urls = _URL_RE.findall(haystack)
        cited = any(term in url for url in urls for term in terms)
    return (mentioned, cited)


def _default_client_factory(timeout_s: float) -> ClientFactory:
    """Дефолтная фабрика клиентов: иностранный egress ⇒ httpx через зарубежный прокси.

    Второй эшелон §6.4 (после `assert_probe_geo`): при иностранном egress без прокси —
    :class:`ProbeGeoViolationError` (клиент не строится, ничего не уходит в сеть).
    """

    def factory(egress: Egress, proxy_url: str | None) -> httpx.AsyncClient:
        if egress == "foreign":
            if not proxy_url:
                msg = "иностранный egress без зарубежного прокси (§6.4/NFR-2): клиент не создан."
                raise ProbeGeoViolationError(msg)
            return httpx.AsyncClient(proxy=proxy_url, timeout=timeout_s)
        return httpx.AsyncClient(timeout=timeout_s)

    return factory


@dataclass(frozen=True, slots=True)
class _PromptCtx:
    """Инвариантный per-(промпт×модель) контекст одного вызова ``run_prompt``."""

    prompt_id: str
    prompt: str
    model: ModelId
    egress: Egress
    brand_terms: tuple[str, ...]


class ProbeRunner:
    """Исполнитель dual-geo probe: промпт×модель → N≥5 :class:`ProbeRun` с §6.4-гарантией."""

    def __init__(
        self,
        *,
        settings: ProbeSettings | None = None,
        llm_settings: LLMRouterSettings | None = None,
        client_factory: ClientFactory | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._settings = settings or get_probe_settings()
        self._llm_settings = llm_settings or get_llm_settings()
        self._client_factory = client_factory or _default_client_factory(
            self._settings.probe_http_timeout_s
        )
        self._clock: Clock = clock or (lambda: datetime.now(tz=UTC))
        self._proxy_cursor = 0

    def _next_proxy(self) -> str | None:
        """Следующий зарубежный прокси из пула (round-robin ротация). Пустой пул ⇒ ``None``."""
        pool = self._settings.proxy_pool()
        if not pool:
            return None
        proxy = pool[self._proxy_cursor % len(pool)]
        self._proxy_cursor += 1
        return proxy

    async def run_prompt(
        self,
        prompt_id: str,
        prompt: str,
        model: ModelId,
        *,
        n_runs: int = MIN_RUNS,
        brand_terms: Sequence[str] | None = None,
    ) -> list[ProbeRun]:
        """N≥5 независимых прогонов промпта на модели → список :class:`ProbeRun` (FR-2.3/AC-3).

        Сбой отдельного прогона изолируется (AC-6): фиксируется error-прогоном, батч живёт.
        Иностранная модель без прокси → error-прогоны (диспатч отклонён §6.4), не РФ-fallback.
        """
        n = max(n_runs, MIN_RUNS)  # §6.7: probe всегда ≥5 прогонов
        terms = brand_terms if brand_terms is not None else self._settings.brand_terms()
        ctx = _PromptCtx(
            prompt_id=prompt_id,
            prompt=prompt,
            model=model,
            egress=egress_for_model(model),  # egress ИЗ модели — вызывающий не задаёт (§6.4)
            brand_terms=tuple(terms),
        )
        runs: list[ProbeRun] = []
        for run_index in range(n):
            proxy = self._next_proxy() if ctx.egress == "foreign" else None
            runs.append(await self._one_run(ctx, run_index, proxy))
        return runs

    async def _one_run(self, ctx: _PromptCtx, run_index: int, proxy: str | None) -> ProbeRun:
        """Один прогон: §6.4-guard → диспатч через P4-адаптер → mention/citation. НЕ бросает."""
        now = self._clock()
        try:
            # СВЯЩЕННЫЙ §6.4/NFR-2 предохранитель ПЕРЕД диспатчем, привязан к фактическому прокси.
            assert_probe_geo(ctx.model, ctx.egress, foreign_proxy_configured=proxy is not None)
            client = self._client_factory(ctx.egress, proxy)
            try:
                provider = make_provider(
                    provider_for_model(ctx.model), self._llm_settings, client=client
                )
                response = await provider.complete(ctx.prompt, task_type="probe")
            finally:
                await client.aclose()
        except ProbeGeoViolationError as exc:
            # Инвариант §6.4 не выполнить (нет прокси) — диспатч отклонён, НЕ РФ-fallback (AC-2).
            logger.warning(
                "probe.geo_refused", prompt_id=ctx.prompt_id, model=ctx.model, run_index=run_index
            )
            return self._error_run(ctx, run_index, now, f"probe_geo: {exc}")
        except ProviderError as exc:
            # Fault isolation (AC-6): сбой провайдера не роняет батч.
            logger.warning(
                "probe.run_failed",
                prompt_id=ctx.prompt_id,
                model=ctx.model,
                run_index=run_index,
                error=str(exc),
            )
            return self._error_run(ctx, run_index, now, f"provider: {exc}")

        mentioned, cited = detect_mention_citation(response.text, ctx.brand_terms)
        return ProbeRun(
            prompt_id=ctx.prompt_id,
            model=ctx.model,
            run_index=run_index,
            raw_response=response.text,
            mentioned=mentioned,
            cited=cited,
            egress=ctx.egress,
            run_at=now,
            error=None,
        )

    @staticmethod
    def _error_run(ctx: _PromptCtx, run_index: int, run_at: datetime, error: str) -> ProbeRun:
        """Собрать error-прогон (fault-isolation / отказ по §6.4): без ответа, с ``error``."""
        return ProbeRun(
            prompt_id=ctx.prompt_id,
            model=ctx.model,
            run_index=run_index,
            raw_response="",
            mentioned=False,
            cited=False,
            egress=ctx.egress,
            run_at=run_at,
            error=error,
        )
