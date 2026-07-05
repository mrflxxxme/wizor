"""Unit: POST /api/v1/sites/{id}/crawl — enqueue-эндпоинт (T7).

Celery-постановка замокана (unit-уровень, брокер не нужен): проверяем контракт
эндпоинта — 202, task_id в теле, tenant из ``X-Tenant-Id``, отказ без тенанта.
Реальный краул/persist — в integration (нужен PG/домен).
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from wizor.crawler import tasks as crawler_tasks


class _FakeAsyncResult:
    """Заглушка Celery ``AsyncResult`` — несёт только ``id``."""

    def __init__(self, task_id: str) -> None:
        self.id = task_id


@pytest.fixture
def captured_enqueue(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Замокать ``crawl_site.delay`` — захватывает аргументы, брокер не трогается."""
    calls: list[tuple[str, str]] = []

    def _fake_delay(site_id: str, tenant_id: str, *_a: Any, **_k: Any) -> _FakeAsyncResult:
        calls.append((site_id, tenant_id))
        return _FakeAsyncResult("task-123")

    monkeypatch.setattr(crawler_tasks.crawl_site, "delay", _fake_delay)
    return calls


@pytest.mark.asyncio
async def test_crawl_enqueues_and_returns_202(
    app_client: AsyncClient, captured_enqueue: list[tuple[str, str]]
) -> None:
    tenant_id = str(uuid.uuid4())
    site_id = str(uuid.uuid4())

    resp = await app_client.post(
        f"/api/v1/sites/{site_id}/crawl", headers={"X-Tenant-Id": tenant_id}
    )

    assert resp.status_code == 202
    body = resp.json()
    assert body["task_id"] == "task-123"
    assert body["site_id"] == site_id
    assert body["status"] == "accepted"
    # Задача поставлена ровно раз с (site_id, tenant_id) из запроса.
    assert captured_enqueue == [(site_id, tenant_id)]


@pytest.mark.asyncio
async def test_crawl_requires_tenant(
    app_client: AsyncClient, captured_enqueue: list[tuple[str, str]]
) -> None:
    site_id = str(uuid.uuid4())

    resp = await app_client.post(f"/api/v1/sites/{site_id}/crawl")

    assert resp.status_code == 400
    # Без тенанта задача НЕ ставится (изоляция §6.8).
    assert captured_enqueue == []


@pytest.mark.asyncio
async def test_crawl_rejects_invalid_site_id(
    app_client: AsyncClient, captured_enqueue: list[tuple[str, str]]
) -> None:
    resp = await app_client.post(
        "/api/v1/sites/not-a-uuid/crawl", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )

    # Path-валидация FastAPI (site_id: uuid.UUID) → 422, задача не ставится.
    assert resp.status_code == 422
    assert captured_enqueue == []
