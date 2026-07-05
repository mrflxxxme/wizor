"""Unit: read-only guard краулера — блокировка не-GET (§6 инвариант 1, AC-7).

Это САКРАЛЬНЫЙ инвариант: краулер физически не выпускает не-GET во внешние домены.
Тесты ассертят, что PUT/POST/DELETE/PATCH поднимают `ReadOnlyViolation` ДО выхода в
сеть, фиксируются в аудит-журнале, и `confirmed_read_only` отражает факт нарушения.
"""

from __future__ import annotations

import httpx
import pytest

from wizor.crawler.guard import (
    BlockedHostError,
    ReadOnlyGuard,
    ReadOnlyTransport,
    ReadOnlyViolation,
    build_guarded_client,
    host_is_blocked,
    is_blocked_ip,
)


def _recording_inner() -> tuple[httpx.MockTransport, list[str]]:
    """Внутренний транспорт, фиксирующий фактически дошедшие до сети методы."""
    reached: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        reached.append(request.method)
        return httpx.Response(200, text="ok")

    return httpx.MockTransport(handler), reached


@pytest.mark.asyncio
async def test_guard_allows_get() -> None:
    guard = ReadOnlyGuard()
    inner, reached = _recording_inner()
    async with build_guarded_client(guard, inner=inner) as client:
        resp = await client.get("https://example.ru/page")
    assert resp.status_code == 200
    assert reached == ["GET"]
    assert guard.confirmed_read_only is True
    assert guard.violations == []


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE", "PATCH"])
@pytest.mark.asyncio
async def test_guard_blocks_non_get(method: str) -> None:
    guard = ReadOnlyGuard()
    inner, reached = _recording_inner()
    async with build_guarded_client(guard, inner=inner) as client:
        with pytest.raises(ReadOnlyViolation):
            await client.request(method, "https://client-site.ru/api")
    # Ключевой ассерт AC-7: не-GET НЕ дошёл до сети.
    assert reached == []
    assert guard.confirmed_read_only is False
    assert len(guard.violations) == 1
    assert guard.violations[0].method == method


@pytest.mark.asyncio
async def test_guard_records_all_attempts() -> None:
    guard = ReadOnlyGuard()
    inner, _ = _recording_inner()
    async with build_guarded_client(guard, inner=inner) as client:
        await client.get("https://example.ru/a")
        with pytest.raises(ReadOnlyViolation):
            await client.post("https://example.ru/b")
    assert [r.method for r in guard.records] == ["GET", "POST"]
    assert [r.allowed for r in guard.records] == [True, False]


@pytest.mark.asyncio
async def test_transport_raises_before_delegating() -> None:
    """ReadOnlyTransport проверяет метод до вызова внутреннего транспорта."""
    guard = ReadOnlyGuard()
    inner, reached = _recording_inner()
    transport = ReadOnlyTransport(guard, inner=inner)
    request = httpx.Request("DELETE", "https://example.ru/resource")
    with pytest.raises(ReadOnlyViolation):
        await transport.handle_async_request(request)
    assert reached == []


# --- F3: SSRF-защита приватных диапазонов (стартовый URL и редирект-хопы) ---


@pytest.mark.parametrize(
    ("ip", "blocked"),
    [
        ("127.0.0.1", True),
        ("10.1.2.3", True),
        ("172.16.0.9", True),
        ("192.168.1.1", True),
        ("169.254.169.254", True),  # AWS/metadata link-local
        ("::1", True),
        ("fc00::1", True),  # ULA
        ("8.8.8.8", False),
        ("93.184.216.34", False),  # example.com
    ],
)
def test_is_blocked_ip(ip: str, *, blocked: bool) -> None:
    assert is_blocked_ip(ip) is blocked


def test_host_is_blocked_literal_ip_no_dns() -> None:
    """Литеральный приватный IP блокируется без резолвера (DNS не дёргается)."""
    assert host_is_blocked("127.0.0.1", None) is True
    assert host_is_blocked("169.254.169.254", None) is True
    # Имя хоста без резолвера — не блокируем (тесты network-free).
    assert host_is_blocked("example.ru", None) is False


def test_host_is_blocked_via_resolver() -> None:
    """Имя хоста, резолвящееся в приватный IP, блокируется (fake-резолвер, без сети)."""
    assert host_is_blocked("internal.corp", lambda _h: ["10.0.0.5"]) is True
    assert host_is_blocked("public.example", lambda _h: ["8.8.8.8"]) is False


@pytest.mark.asyncio
async def test_transport_blocks_private_start_url() -> None:
    """Прямой запрос к приватному IP отклоняется до сети и фиксируется в guard."""
    guard = ReadOnlyGuard()
    inner, reached = _recording_inner()
    transport = ReadOnlyTransport(guard, inner=inner)
    request = httpx.Request("GET", "http://169.254.169.254/latest/meta-data/")
    with pytest.raises(BlockedHostError):
        await transport.handle_async_request(request)
    assert reached == []  # до сети не дошло
    assert len(guard.blocked) == 1
    assert "169.254.169.254" in guard.blocked[0].url


@pytest.mark.asyncio
async def test_client_blocks_redirect_to_private_ip() -> None:
    """3xx-редирект на приватный IP отклоняется на хопе — тело не сохраняется."""
    reached: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        reached.append(str(request.url))
        if request.url.host == "client-site.ru":
            # Клиентский сайт редиректит GET на metadata-эндпоинт.
            return httpx.Response(302, headers={"location": "http://169.254.169.254/creds"})
        return httpx.Response(200, text="secret")

    guard = ReadOnlyGuard()
    inner = httpx.MockTransport(handler)
    async with build_guarded_client(guard, inner=inner) as client:
        with pytest.raises(BlockedHostError):
            await client.get("https://client-site.ru/")
    # Первый хоп дошёл (публичный), но редирект-цель (169.254…) НЕ фетчилась.
    assert reached == ["https://client-site.ru/"]
    assert any("169.254.169.254" in b.url for b in guard.blocked)
