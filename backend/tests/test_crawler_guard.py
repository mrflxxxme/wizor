"""Unit: read-only guard краулера — блокировка не-GET (§6 инвариант 1, AC-7).

Это САКРАЛЬНЫЙ инвариант: краулер физически не выпускает не-GET во внешние домены.
Тесты ассертят, что PUT/POST/DELETE/PATCH поднимают `ReadOnlyViolation` ДО выхода в
сеть, фиксируются в аудит-журнале, и `confirmed_read_only` отражает факт нарушения.
"""

from __future__ import annotations

import httpx
import pytest

from wizor.crawler.guard import (
    ReadOnlyGuard,
    ReadOnlyTransport,
    ReadOnlyViolation,
    build_guarded_client,
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
