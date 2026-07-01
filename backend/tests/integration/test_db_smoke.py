"""Integration (live-gold): Postgres+pgvector, миграция, multi-tenant изоляция.

Помечены ``integration`` — запускаются в CI против реального Postgres (services).
Предусловие (CI): ``alembic upgrade head`` + ``python -m wizor.iam.seed`` выполнены.
Покрывают AC-6 (изоляция), AC-8 (pgvector), FR-P1-2/5.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text

from wizor.db.session import get_engine, get_sessionmaker
from wizor.iam.models import Site
from wizor.iam.seed import TEST_TENANT_ID, count_foreign_tenant_sites

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_pgvector_extension_active() -> None:
    """AC-8: pgvector работает — vector_dims('[1,2,3]') == 3."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT vector_dims('[1,2,3]'::vector)"))
        assert result.scalar_one() == 3


@pytest.mark.asyncio
async def test_seed_tenant_present() -> None:
    """FR-P1-2: тестовый тенант засеян и доступен."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT count(*) FROM tenants WHERE id = :tid"),
            {"tid": str(TEST_TENANT_ID)},
        )
        assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_multitenant_isolation_ac6() -> None:
    """AC-6: после сида только тестового тенанта чужих sites нет (0 строк)."""
    assert await count_foreign_tenant_sites() == 0


@pytest.mark.asyncio
async def test_isolation_holds_with_second_tenant() -> None:
    """Изоляция при наличии второго тенанта: фильтр по tenant_id не протекает.

    Вставляем сайт другого тенанта и проверяем, что запрос, ограниченный
    TEST_TENANT_ID, его не возвращает (§6.8). Затем убираем за собой.
    """
    other_tenant = uuid.uuid4()
    other_site_id = uuid.uuid4()
    sessionmaker = get_sessionmaker()

    # Вставляем «чужой» тенант + сайт (FK требует существующего тенанта).
    async with sessionmaker() as session:
        await session.execute(
            text(
                "INSERT INTO tenants (id, name, slug, created_at, updated_at) "
                "VALUES (:id, :name, :slug, now(), now())"
            ),
            {"id": str(other_tenant), "name": "Other", "slug": f"other-{other_tenant}"},
        )
        await session.execute(
            text(
                "INSERT INTO sites (id, tenant_id, url, created_at, updated_at) "
                "VALUES (:id, :tid, :url, now(), now())"
            ),
            {"id": str(other_site_id), "tid": str(other_tenant), "url": "https://other.test"},
        )
        await session.commit()

    try:
        async with sessionmaker() as session:
            scoped = await session.execute(select(Site).where(Site.tenant_id == TEST_TENANT_ID))
            urls = {s.url for s in scoped.scalars().all()}
            assert "https://other.test" not in urls
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": str(other_tenant)}
            )
            await session.commit()
