"""Read-only enforcement краулера (§6 инвариант 1, AC-7).

Структурная (не по соглашению) гарантия: HTTP-клиент краулера выпускает во внешние
домены ТОЛЬКО метод GET. Любой не-GET (PUT/POST/DELETE/PATCH/…) перехватывается на
уровне httpx-транспорта, ДО выхода в сеть — поднимается :class:`ReadOnlyViolation`
и запись фиксируется в аудит-журнале guard'а.

Guard — единственный источник истины для `CrawlResult.read_only_confirmed`:
`confirmed_read_only` истинно тогда и только тогда, когда за весь краул не было ни
одной попытки не-GET. Тест AC-7 ассертит именно это.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

# Единственный разрешённый HTTP-метод к внешним/клиентским доменам (§6.1).
_ALLOWED_METHOD = "GET"


class ReadOnlyViolation(RuntimeError):  # noqa: N818 — имя закреплено контрактом фазы (AC-7)
    """Попытка не-GET запроса к внешнему домену — нарушение read-only."""


@dataclass(frozen=True)
class RequestRecord:
    """Запись аудит-журнала об одной попытке HTTP-запроса."""

    method: str
    url: str
    allowed: bool


@dataclass
class ReadOnlyGuard:
    """Аудит-журнал + арбитр read-only инварианта краула.

    Держит след всех попыток запросов. Не-GET фиксируется как нарушение и блокируется.
    """

    _records: list[RequestRecord] = field(default_factory=list)

    @property
    def records(self) -> list[RequestRecord]:
        """Полный след запросов (для аудита/логов)."""
        return list(self._records)

    @property
    def violations(self) -> list[RequestRecord]:
        """Только зафиксированные нарушения (не-GET)."""
        return [r for r in self._records if not r.allowed]

    @property
    def confirmed_read_only(self) -> bool:
        """True = ноль не-GET запросов за краул (AC-7, основа `read_only_confirmed`)."""
        return not self.violations

    def check(self, method: str, url: str) -> None:
        """Проверить метод: разрешить GET, иначе зафиксировать и поднять исключение."""
        allowed = method.upper() == _ALLOWED_METHOD
        self._records.append(RequestRecord(method=method.upper(), url=url, allowed=allowed))
        if not allowed:
            msg = (
                f"read-only нарушение: метод {method.upper()} на {url!r}; "
                f"краулеру разрешён только {_ALLOWED_METHOD}"
            )
            raise ReadOnlyViolation(msg)


class ReadOnlyTransport(httpx.AsyncBaseTransport):
    """httpx-транспорт-обёртка: пропускает только GET, остальное → ReadOnlyViolation.

    Оборачивает внутренний транспорт. Проверка выполняется ДО делегирования, значит
    не-GET физически не уходит в сеть.
    """

    def __init__(
        self,
        guard: ReadOnlyGuard,
        inner: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._guard = guard
        self._inner = inner if inner is not None else httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Точка структурного enforcement: не-GET поднимет исключение здесь.
        self._guard.check(request.method, str(request.url))
        return await self._inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self._inner.aclose()


def build_guarded_client(
    guard: ReadOnlyGuard,
    *,
    inner: httpx.AsyncBaseTransport | None = None,
    timeout_s: float = 30.0,
) -> httpx.AsyncClient:
    """Собрать `AsyncClient`, все запросы которого проходят через read-only guard.

    `inner` позволяет подменить нижний транспорт (в тестах — `httpx.MockTransport`),
    не ослабляя guard: обёртка всё равно блокирует не-GET.
    """
    transport = ReadOnlyTransport(guard, inner=inner)
    # follow_redirects=True безопасно: httpx следует по GET-редиректам, метод остаётся GET.
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(timeout_s),
        follow_redirects=True,
        headers={"User-Agent": "WizorBot/0.1 (+https://wizor.ru/bot; read-only audit)"},
    )
