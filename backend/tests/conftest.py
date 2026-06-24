"""Общие фикстуры тестов backend.

``app_client`` поднимает приложение через ASGI-транспорт + lifespan без сети
(PostHog-ключ пуст → no-op). Не требует Postgres/Redis — это уровень unit.
Integration-тесты (метка ``integration``) используют реальные сервисы в CI.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from wizor.main import create_app


@pytest.fixture
async def app_client() -> AsyncIterator[AsyncClient]:
    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
