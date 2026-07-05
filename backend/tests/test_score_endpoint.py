"""Unit: GET /api/v1/sites/{id}/score — контракт эндпоинта (T5).

Репозиторий замокан (unit-уровень, PG не нужен), сессия подменена через
``dependency_overrides``: проверяем контракт — 200 с {score, components, projection},
404 без краула, 400 без тенанта, 422 на невалидный site_id. Реальный persist/изоляция —
в integration.
"""

from __future__ import annotations

import types
import uuid
from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from wizor.db.session import get_session
from wizor.main import create_app
from wizor.scoring import repository


class _FakeSession:
    """Заглушка AsyncSession — эндпоинт лишь коммитит (репозиторий замокан)."""

    async def commit(self) -> None:
        return None


def _canned_audit() -> list[dict[str, object]]:
    return [
        {"factor": "robots_txt", "verdict": "pass", "detail": "", "data": {}},
        {"factor": "faq", "verdict": "warn", "detail": "", "data": {}},
        {"factor": "json_ld", "verdict": "fail", "detail": "", "data": {}},
    ]


@pytest.fixture
def patched_repo(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Замокать репозиторий: краул есть, url известен, persist — no-op с захватом."""
    saved: dict[str, object] = {}

    async def _load_latest_crawl(*_a: object, **_k: object) -> object:
        return types.SimpleNamespace(audit_summary_json=_canned_audit())

    async def _load_site_url(*_a: object, **_k: object) -> str:
        return "https://example.test"

    async def _save(*_a: object, **kwargs: object) -> object:
        saved["result"] = kwargs.get("result")
        return object()

    monkeypatch.setattr(repository, "load_latest_crawl", _load_latest_crawl)
    monkeypatch.setattr(repository, "load_site_url", _load_site_url)
    monkeypatch.setattr(repository, "save_score_result", _save)
    return saved


@pytest.fixture
async def score_client(patched_repo: dict[str, object]) -> AsyncIterator[AsyncClient]:
    """Клиент с подменённой сессией — БД не требуется."""
    app = create_app()
    app.dependency_overrides[get_session] = lambda: _FakeSession()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.mark.asyncio
async def test_score_returns_200_shape(score_client: AsyncClient) -> None:
    """200: тело содержит score, компоненты и проекцию (AC-3/AC-4 форма)."""
    resp = await score_client.get(
        f"/api/v1/sites/{uuid.uuid4()}/score", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body["score"], (int, float))
    assert 0.0 <= body["score"] <= 100.0
    assert body["score_version"]
    assert len(body["components"]) > 0
    assert {"name", "weight", "value", "verdict", "description"} <= set(body["components"][0])
    # Проекция для warn/fail факторов (faq, json_ld) присутствует.
    assert {p["fix_id"] for p in body["projection"]} == {"fix_faq", "fix_json_ld"}


@pytest.mark.asyncio
async def test_score_404_when_no_crawl(
    score_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """404: нет crawl_results для сайта — скорить нечего."""

    async def _none(*_a: object, **_k: object) -> None:
        return None

    monkeypatch.setattr(repository, "load_latest_crawl", _none)
    resp = await score_client.get(
        f"/api/v1/sites/{uuid.uuid4()}/score", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_score_400_when_no_tenant(score_client: AsyncClient) -> None:
    """400: без X-Tenant-Id скорить нельзя (изоляция §6.8)."""
    resp = await score_client.get(f"/api/v1/sites/{uuid.uuid4()}/score")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_score_422_when_bad_site_id(score_client: AsyncClient) -> None:
    """422: невалидный site_id отсекается path-валидацией FastAPI."""
    resp = await score_client.get(
        "/api/v1/sites/not-a-uuid/score", headers={"X-Tenant-Id": str(uuid.uuid4())}
    )
    assert resp.status_code == 422
