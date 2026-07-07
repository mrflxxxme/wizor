"""Unit: metrics-роутер — Visibility + управление наборами промптов (T6).

Репозитории замоканы (unit-уровень, PG не нужен), сессия подменена через
``dependency_overrides``: проверяем контракт — 200/400/404 для visibility (AC-4) и
версионирование набора промптов (AC-5). Реальный persist/изоляция — в integration.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from wizor.db.session import get_session
from wizor.main import create_app
from wizor.metrics import repository as metrics_repository
from wizor.metrics.schemas import VisibilityComponents, VisibilityMetrics
from wizor.probe import repository as probe_repository
from wizor.probe.schemas import PromptSetDTO


class _FakeSession:
    """Заглушка AsyncSession — эндпоинт лишь коммитит (репозиторий замокан)."""

    async def commit(self) -> None:
        return None


def _sample_metrics() -> VisibilityMetrics:
    return VisibilityMetrics(
        visibility_score=72.5,
        components=VisibilityComponents(coverage=0.8, sov=0.8, citation_rate=0.5, stability=0.9),
        ci_lower=68.0,
        ci_upper=77.0,
        n=20,
        prompt_set_version=3,
    )


@pytest.fixture
async def metrics_client() -> AsyncIterator[AsyncClient]:
    """Клиент с подменённой сессией — БД не требуется."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: _FakeSession()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
async def test_visibility_200_shape(
    metrics_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """200: тело несёт score, 4 компонента, CI, n, версию (AC-4 форма)."""

    async def _load(*_a: object, **_k: object) -> VisibilityMetrics:
        return _sample_metrics()

    monkeypatch.setattr(metrics_repository, "load_latest_visibility", _load)
    resp = await metrics_client.get(
        f"/api/v1/sites/{uuid.uuid4()}/visibility", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert 0.0 <= body["visibility_score"] <= 100.0
    assert {"coverage", "sov", "citation_rate", "stability", "has_competitor_data"} == set(
        body["components"]
    )
    # F2 (§6.2 honest-forecast): API отдаёт флаг, чтобы фронт не выдал sov-прокси за реальную долю.
    assert body["components"]["has_competitor_data"] is False
    assert body["ci_lower"] <= body["ci_upper"]
    assert body["n"] == 20
    assert body["prompt_set_version"] == 3


@pytest.mark.asyncio
async def test_visibility_404_when_no_metrics(
    metrics_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """404: агрегата ещё нет — probe не прогонялся."""

    async def _none(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(metrics_repository, "load_latest_visibility", _none)
    resp = await metrics_client.get(
        f"/api/v1/sites/{uuid.uuid4()}/visibility", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_visibility_400_when_no_tenant(metrics_client: AsyncClient) -> None:
    """400: без X-Tenant-Id доступа к метрикам нет (изоляция §6.8)."""
    resp = await metrics_client.get(f"/api/v1/sites/{uuid.uuid4()}/visibility")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_visibility_422_when_bad_site_id(metrics_client: AsyncClient) -> None:
    """422: невалидный site_id отсекается path-валидацией FastAPI."""
    resp = await metrics_client.get(
        "/api/v1/sites/not-a-uuid/visibility", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_prompts_404_when_absent(
    metrics_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """404: у сайта ещё нет набора промптов."""

    async def _none(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(probe_repository, "load_active_prompt_set", _none)
    resp = await metrics_client.get(
        f"/api/v1/sites/{uuid.uuid4()}/prompts", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_prompts_creates_new_version_ac5(
    metrics_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AC-5: PUT набора возвращает новую версию (upsert → версия 2)."""
    site_id = uuid.uuid4()

    async def _upsert(*_a: object, **kwargs: object) -> PromptSetDTO:
        prompts = kwargs["prompts"]
        assert isinstance(prompts, list)
        return PromptSetDTO(id=str(uuid.uuid4()), site_id=str(site_id), version=2, prompts=prompts)

    monkeypatch.setattr(probe_repository, "upsert_prompt_set", _upsert)
    resp = await metrics_client.put(
        f"/api/v1/sites/{site_id}/prompts",
        headers={"X-Tenant-Id": str(uuid.uuid4())},
        json={"prompts": ["куда сдать макулатуру", "лучший сервис вывоза"]},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == 2
    assert len(body["prompts"]) == 2


@pytest.mark.asyncio
async def test_put_prompts_400_when_no_tenant(metrics_client: AsyncClient) -> None:
    """400: правка набора промптов без тенанта запрещена (§6.8)."""
    resp = await metrics_client.put(
        f"/api/v1/sites/{uuid.uuid4()}/prompts", json={"prompts": ["x"]}
    )
    assert resp.status_code == 400
