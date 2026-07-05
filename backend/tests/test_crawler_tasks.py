"""Unit: tenant-scoping задачи crawl (F5, §6.8) — быстрое покрытие без live-PG.

`_load_site_url` фильтрует `Site.tenant_id == tenant_id`. Ключ изоляции: чужой тенант →
`LookupError` (задача НЕ ставится в очередь, чужой сайт не краулится). Async-сессия и
запрос замоканы — тест не требует Postgres.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

import wizor.crawler.tasks as tasks


class _FakeResult:
    def __init__(self, value: Any) -> None:
        self._value = value

    def scalar_one_or_none(self) -> Any:
        return self._value


class _FakeSession:
    def __init__(self, value: Any) -> None:
        self._value = value
        self.executed: list[Any] = []

    async def __aenter__(self) -> _FakeSession:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        return None

    async def execute(self, stmt: Any) -> _FakeResult:
        self.executed.append(stmt)
        return _FakeResult(self._value)


def _fake_sessionmaker(value: Any) -> Any:
    """Вернуть callable-sessionmaker, отдающий сессию со `scalar_one_or_none()==value`."""

    def _maker() -> _FakeSession:
        return _FakeSession(value)

    return _maker


@pytest.mark.asyncio
async def test_load_site_url_foreign_tenant_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Чужой tenant_id → строка не найдена → LookupError (без enqueue краула)."""
    # scalar_one_or_none() == None ⇔ WHERE tenant_id=... не совпал (изоляция сработала).
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: _fake_sessionmaker(None))
    with pytest.raises(LookupError):
        await tasks._load_site_url(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_load_site_url_own_tenant_returns_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Свой tenant_id → URL возвращается (позитивный контроль изоляции)."""
    monkeypatch.setattr(tasks, "get_sessionmaker", lambda: _fake_sessionmaker("https://acme.ru"))
    url = await tasks._load_site_url(uuid.uuid4(), uuid.uuid4())
    assert url == "https://acme.ru"
