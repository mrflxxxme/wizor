"""Read-only enforcement краулера (§6 инвариант 1, AC-7) + SSRF-защита хостов.

Гарантия read-only **для httpx-пути** структурна (не по соглашению): HTTP-клиент
краулера выпускает во внешние домены ТОЛЬКО метод GET. Любой не-GET
(PUT/POST/DELETE/PATCH/…) перехватывается на уровне httpx-транспорта, ДО выхода в
сеть — поднимается :class:`ReadOnlyViolation`, запись фиксируется в аудит-журнале.

Browser-путь (Playwright) enforce'ится отдельно, route-хендлером в `fetch.py`, который
пишет метод каждого browser-запроса в ЭТОТ ЖЕ `ReadOnlyGuard` (`guard.record`) и рвёт
не-GET на уровне Chromium (`route.abort`). Поэтому `confirmed_read_only` покрывает и
httpx-, и browser-трафик: истинно ⇔ за весь краул не было ни одного не-GET.

Дополнительно транспорт блокирует SSRF: хосты, резолвящиеся в loopback/приватные/
link-local диапазоны (в т.ч. 169.254.169.254 metadata), отклоняются ДО сети —
и для стартового URL, и для каждого редирект-хопа (httpx вызывает транспорт на хоп).
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass, field

import httpx

# Единственный разрешённый HTTP-метод к внешним/клиентским доменам (§6.1).
_ALLOWED_METHOD = "GET"

# Резолвер имени хоста в список IP-строк (инъектируется в тестах без DNS).
Resolver = Callable[[str], list[str]]

_UNSET: object = object()


class ReadOnlyViolation(RuntimeError):  # noqa: N818 — имя закреплено контрактом фазы (AC-7)
    """Попытка не-GET запроса к внешнему домену — нарушение read-only."""


class BlockedHostError(httpx.HTTPError):
    """Хост резолвится в приватный/loopback/link-local диапазон — SSRF-защита, запрос отклонён.

    Наследует ``httpx.HTTPError``, поэтому обходчик ловит его в общем ``except httpx.HTTPError``
    и пропускает страницу (fault-isolated), не роняя батч.
    """


@dataclass(frozen=True)
class RequestRecord:
    """Запись аудит-журнала об одной попытке HTTP-запроса."""

    method: str
    url: str
    allowed: bool


@dataclass(frozen=True)
class BlockedRecord:
    """Запись о запросе, заблокированном SSRF-фильтром (приватный диапазон)."""

    url: str
    reason: str


def is_blocked_ip(ip_str: str) -> bool:
    """True, если IP принадлежит небезопасному диапазону (loopback/private/link-local/reserved).

    Покрывает 127.0.0.0/8, 10/8, 172.16/12, 192.168/16, 169.254.0.0/16 (incl.
    169.254.169.254 metadata), ::1, fc00::/7 и прочие зарезервированные диапазоны.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved


def default_resolver(host: str) -> list[str]:
    """Штатный DNS-резолвер: имя хоста → список IP-строк (блокирующий socket-вызов)."""
    infos = socket.getaddrinfo(host, None)
    return [str(info[4][0]) for info in infos]


def host_is_blocked(host: str | None, resolver: Resolver | None) -> bool:
    """Проверить хост на принадлежность небезопасному диапазону (литерал IP или резолв).

    Литеральный IP проверяется всегда. Для имени хоста DNS-резолв выполняется только если
    задан `resolver` (в проде — реальный; в тестах с мок-транспортом — None, DNS не дёргаем).
    Нерезолвимое имя блокируется консервативно (лучше отказать, чем словить SSRF).
    """
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        return is_blocked_ip(host)
    if resolver is None:
        return False
    try:
        ips = resolver(host)
    except OSError:
        return True
    return any(is_blocked_ip(ip) for ip in ips)


@dataclass
class ReadOnlyGuard:
    """Аудит-журнал + арбитр read-only инварианта краула (httpx + browser).

    Держит след всех попыток запросов (обоих путей) и список SSRF-блокировок. Не-GET
    фиксируется как нарушение; httpx-путь дополнительно рвёт его исключением.
    """

    _records: list[RequestRecord] = field(default_factory=list)
    _blocked: list[BlockedRecord] = field(default_factory=list)

    @property
    def records(self) -> list[RequestRecord]:
        """Полный след запросов httpx + browser (для аудита/логов)."""
        return list(self._records)

    @property
    def violations(self) -> list[RequestRecord]:
        """Только зафиксированные нарушения (не-GET)."""
        return [r for r in self._records if not r.allowed]

    @property
    def blocked(self) -> list[BlockedRecord]:
        """Запросы, отклонённые SSRF-фильтром (приватный диапазон)."""
        return list(self._blocked)

    @property
    def confirmed_read_only(self) -> bool:
        """True = ноль не-GET запросов за краул (AC-7, основа `read_only_confirmed`)."""
        return not self.violations

    def record(self, method: str, url: str) -> bool:
        """Зафиксировать попытку запроса в журнале; вернуть allowed (GET?). НЕ бросает.

        Единая точка учёта для httpx- и browser-путей. Browser-route-хендлер использует
        именно её (тихо, без исключения — не-GET он рвёт средствами Chromium).
        """
        allowed = method.upper() == _ALLOWED_METHOD
        self._records.append(RequestRecord(method=method.upper(), url=url, allowed=allowed))
        return allowed

    def note_blocked(self, url: str, reason: str) -> None:
        """Зафиксировать SSRF-блокировку хоста (для аудита; сам запрос не выполняется)."""
        self._blocked.append(BlockedRecord(url=url, reason=reason))

    def check(self, method: str, url: str) -> None:
        """httpx-путь: зафиксировать метод и поднять исключение на не-GET (structural block)."""
        if not self.record(method, url):
            msg = (
                f"read-only нарушение: метод {method.upper()} на {url!r}; "
                f"краулеру разрешён только {_ALLOWED_METHOD}"
            )
            raise ReadOnlyViolation(msg)


class ReadOnlyTransport(httpx.AsyncBaseTransport):
    """httpx-транспорт-обёртка: пропускает только GET к безопасным хостам.

    Двойной enforcement ДО делегирования (значит, ничего не уходит в сеть при отказе):
    1. не-GET → :class:`ReadOnlyViolation`;
    2. хост в приватном/loopback/link-local диапазоне → :class:`BlockedHostError` (SSRF).
    Проверка выполняется на КАЖДЫЙ запрос, включая редирект-хопы (httpx зовёт транспорт
    на каждый хоп), поэтому редирект на внутренний/metadata-хост тоже блокируется.
    """

    def __init__(
        self,
        guard: ReadOnlyGuard,
        inner: httpx.AsyncBaseTransport | None = None,
        *,
        resolver: Resolver | None = None,
    ) -> None:
        self._guard = guard
        self._inner = inner if inner is not None else httpx.AsyncHTTPTransport()
        self._resolver = resolver

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        # Точка структурного enforcement: не-GET поднимет исключение здесь.
        self._guard.check(request.method, str(request.url))
        host = request.url.host
        if await asyncio.to_thread(host_is_blocked, host, self._resolver):
            reason = f"приватный/loopback/link-local хост {host!r} (SSRF-защита)"
            self._guard.note_blocked(str(request.url), reason)
            raise BlockedHostError(reason)
        return await self._inner.handle_async_request(request)

    async def aclose(self) -> None:
        await self._inner.aclose()


def build_guarded_client(
    guard: ReadOnlyGuard,
    *,
    inner: httpx.AsyncBaseTransport | None = None,
    timeout_s: float = 30.0,
    resolver: Resolver | None | object = _UNSET,
) -> httpx.AsyncClient:
    """Собрать `AsyncClient`, все запросы которого проходят через read-only + SSRF guard.

    `inner` позволяет подменить нижний транспорт (в тестах — `httpx.MockTransport`),
    не ослабляя guard: обёртка всё равно блокирует не-GET. По умолчанию DNS-резолв для
    SSRF-фильтра включён только на реальном транспорте (`inner is None`); при инъекции
    мок-транспорта резолв отключён (тесты network-free), но литеральные приватные IP
    блокируются всегда.
    """
    if resolver is _UNSET:
        effective_resolver: Resolver | None = default_resolver if inner is None else None
    else:
        effective_resolver = resolver  # type: ignore[assignment]
    transport = ReadOnlyTransport(guard, inner=inner, resolver=effective_resolver)
    # follow_redirects=True безопасно: httpx следует по GET-редиректам (метод остаётся GET),
    # а каждый хоп повторно проходит SSRF-проверку транспорта (редирект на 127.0.0.1 отклонён).
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(timeout_s),
        follow_redirects=True,
        headers={"User-Agent": "WizorBot/0.1 (+https://wizor.ru/bot; read-only audit)"},
    )
