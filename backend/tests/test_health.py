"""Unit: /health и tenancy-middleware (AC-4)."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_without_tenant(app_client: AsyncClient) -> None:
    resp = await app_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["tenant"] is None
    assert body["data_region"] == "ru-central1"


@pytest.mark.asyncio
async def test_health_with_tenant_header(app_client: AsyncClient) -> None:
    tenant_id = str(uuid.uuid4())
    resp = await app_client.get("/health", headers={"X-Tenant-Id": tenant_id})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["tenant"] == tenant_id


@pytest.mark.asyncio
async def test_health_ignores_invalid_tenant(app_client: AsyncClient) -> None:
    resp = await app_client.get("/health", headers={"X-Tenant-Id": "not-a-uuid"})
    assert resp.status_code == 200
    # Невалидный заголовок → tenant=None (а не падение запроса).
    assert resp.json()["tenant"] is None
