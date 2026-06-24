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


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-зависимость: выдаёт сессию и гарантированно закрывает её."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session
