"""Async-движок и фабрика сессий (SQLAlchemy 2.x / asyncpg).

Движок создаётся лениво (на первый запрос), чтобы импорт модуля не требовал
доступной БД — это позволяет гонять unit-тесты и собирать приложение без Postgres.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from wizor.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Вернуть (создав при необходимости) общий async-движок."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Вернуть (создав при необходимости) фабрику async-сессий."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(), expire_on_commit=False, class_=AsyncSession
        )
    return _sessionmaker


async def dispose_engine() -> None:
    """Закрыть и сбросить кешированные движок/фабрику сессий.

    Обязательный финал Celery-задач: каждая задача выполняется в собственном
    ``asyncio.run``-loop'е, а модульный кеш живёт дольше задачи — движок,
    созданный в уже закрытом loop'е, на следующей задаче того же воркера даёт
    asyncpg «got Future attached to a different loop». FastAPI-процессу сброс
    не нужен (uvicorn держит один loop); тест-харнесс делает то же самое в
    ``tests/integration/conftest.fresh_engine``.
    """
    global _engine, _sessionmaker
    engine = _engine
    _engine = None
    _sessionmaker = None
    if engine is not None:
        await engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-зависимость: выдаёт сессию и гарантированно закрывает её."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
