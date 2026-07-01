"""Фикстуры integration-тестов: свежий async-движок на каждый тест.

pytest-asyncio (auto) даёт каждому тесту собственный event loop. Модульный кеш
движка/sessionmaker (`wizor.db.session`) иначе переиспользуется между петлями →
asyncpg падает с 'got Future attached to a different loop'. Это исключительно
тест-харнесс-эффект (в проде uvicorn держит один loop на весь процесс), поэтому
лечим на уровне тестов: сбрасываем кеш до теста и диспоузим движок после — каждый
тест создаёт движок в своём текущем loop.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

import wizor.db.session as db_session


@pytest.fixture(autouse=True)
async def fresh_engine() -> AsyncIterator[None]:
    db_session._engine = None
    db_session._sessionmaker = None
    yield
    engine = db_session._engine
    if engine is not None:
        await engine.dispose()
    db_session._engine = None
    db_session._sessionmaker = None
