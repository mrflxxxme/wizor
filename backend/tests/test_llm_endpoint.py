"""Unit: GET /api/v1/llm/route + /api/v1/llm/providers — контракт эндпоинтов (P4).

Доменный ``LLMRouter`` и репозиторий замоканы (unit-уровень, PG не нужен), сессия
подменена через ``dependency_overrides``. Проверяем контракт: превью маршрутизации
(200 с провайдером; AC-1 дефолт RU, AC-2 opt-in override), мягкая деградация при
недоступном роутере (200 resolved=false), 400 без тенанта, список провайдеров.
Реальный persist/изоляция — в integration (test_provider_configs).
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from wizor.db.session import get_session
from wizor.llm_router import repository, router_api
from wizor.llm_router.schemas import Provider, ProviderConfigDTO, TaskType
from wizor.main import create_app


class _FakeSession:
    """Заглушка AsyncSession — эндпоинты read-only, репозиторий замокан."""

    async def commit(self) -> None:
        return None


class _FakeRouter:
    """Мок доменного LLMRouter: дефолт RU (AC-1), override honored (AC-2)."""

    def __init__(self, default: Provider = "gigachat") -> None:
        self._default = default

    async def preview_route(
        self,
        *,
        task_type: TaskType,
        tenant_configs: list[ProviderConfigDTO],
        provider_override: Provider | None,
    ) -> Provider:
        _ = (task_type, tenant_configs)
        if provider_override is not None:
            return provider_override
        return self._default


@pytest.fixture
def patched_repo(monkeypatch: pytest.MonkeyPatch) -> list[ProviderConfigDTO]:
    """Замокать репозиторий: отдаём фиксированный список оверрайдов тенанта."""
    configs = [
        ProviderConfigDTO(
            tenant_id="00000000-0000-0000-0000-000000000001",
            task_type="content_gen",
            provider="gigachat",
            enabled=True,
        )
    ]

    async def _load(*_a: object, **_k: object) -> list[ProviderConfigDTO]:
        return configs

    monkeypatch.setattr(repository, "load_provider_configs", _load)
    return configs


@pytest.fixture
async def llm_client(patched_repo: list[ProviderConfigDTO]) -> AsyncIterator[AsyncClient]:
    """Клиент с подменённой сессией — БД не требуется."""
    _ = patched_repo
    app = create_app()
    app.dependency_overrides[get_session] = lambda: _FakeSession()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
async def test_route_preview_default_ru(
    llm_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-1: content_gen без override → RU-провайдер; тело имеет полную форму, resolved=true."""
    monkeypatch.setattr(router_api, "_load_router", lambda: _FakeRouter())
    resp = await llm_client.get(
        "/api/v1/llm/route",
        params={"task_type": "content_gen"},
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["task_type"] == "content_gen"
    assert body["provider"] == "gigachat"
    assert body["resolved"] is True
    assert body["override_applied"] is False
    assert set(body) == {"task_type", "provider", "override_applied", "resolved", "detail"}


@pytest.mark.asyncio
async def test_route_preview_override_applied(
    llm_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-2: явный opt-in override → провайдер = override, override_applied=true."""
    monkeypatch.setattr(router_api, "_load_router", lambda: _FakeRouter())
    resp = await llm_client.get(
        "/api/v1/llm/route",
        params={"task_type": "batch", "provider_override": "openai"},
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["provider"] == "openai"
    assert body["override_applied"] is True
    assert body["resolved"] is True


@pytest.mark.asyncio
async def test_route_preview_router_unavailable(
    llm_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Доменный роутер недоступен → мягкий 200 (resolved=false, provider=null)."""
    monkeypatch.setattr(router_api, "_load_router", lambda: None)
    resp = await llm_client.get(
        "/api/v1/llm/route",
        params={"task_type": "content_gen"},
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["resolved"] is False
    assert body["provider"] is None


@pytest.mark.asyncio
async def test_route_preview_400_when_no_tenant(llm_client: AsyncClient) -> None:
    """400: без X-Tenant-Id маршрутизировать нельзя (изоляция §6.8)."""
    resp = await llm_client.get("/api/v1/llm/route", params={"task_type": "content_gen"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_route_preview_422_when_bad_task_type(llm_client: AsyncClient) -> None:
    """422: невалидный task_type отсекается валидацией Literal (schemas)."""
    resp = await llm_client.get(
        "/api/v1/llm/route",
        params={"task_type": "not-a-task"},
        headers={"X-Tenant-Id": str(uuid.uuid4())},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_providers_returns_configs(
    llm_client: AsyncClient, patched_repo: list[ProviderConfigDTO]
) -> None:
    """200: список routing-оверрайдов тенанта в форме ProviderConfigDTO."""
    resp = await llm_client.get("/api/v1/llm/providers", headers={"X-Tenant-Id": str(uuid.uuid4())})

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(patched_repo)
    assert body[0]["provider"] == "gigachat"
    assert {"tenant_id", "task_type", "provider", "enabled"} <= set(body[0])


@pytest.mark.asyncio
async def test_list_providers_400_when_no_tenant(llm_client: AsyncClient) -> None:
    """400: список провайдеров требует тенанта (§6.8)."""
    resp = await llm_client.get("/api/v1/llm/providers")
    assert resp.status_code == 400
