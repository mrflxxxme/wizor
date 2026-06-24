"""Идемпотентный сид тестового тенанта (для dev-bootstrap и integration-smoke).

Создаёт фиксированный тенант ``TEST_TENANT_ID`` с одним пользователем и сайтом.
Идемпотентность: повторный запуск не плодит дубли (проверка по PK). Запуск:
``python -m wizor.iam.seed``.
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from sqlalchemy import select

from wizor.db.session import get_sessionmaker
from wizor.iam.models import Site, Tenant, User

logger = structlog.get_logger(__name__)

# Фиксированные ID — чтобы integration-тесты ссылались на известный тенант (AC-6).
TEST_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
TEST_SITE_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")


async def seed() -> None:
    """Создать тестовый тенант/пользователя/сайт, если их ещё нет."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        existing = await session.get(Tenant, TEST_TENANT_ID)
        if existing is not None:
            logger.info("seed_skip", reason="tenant_exists", tenant_id=str(TEST_TENANT_ID))
            return

        tenant = Tenant(id=TEST_TENANT_ID, name="WIZOR Test Tenant", slug="wizor-test")
        user = User(
            id=TEST_USER_ID,
            tenant_id=TEST_TENANT_ID,
            email="founder@wizor.test",
        )
        site = Site(
            id=TEST_SITE_ID,
            tenant_id=TEST_TENANT_ID,
            url="https://example.test",
        )
        session.add_all([tenant, user, site])
        await session.commit()
        logger.info("seed_done", tenant_id=str(TEST_TENANT_ID))


async def count_foreign_tenant_sites() -> int:
    """Helper для AC-6: число sites НЕ принадлежащих тестовому тенанту (ожидается 0)."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        result = await session.execute(select(Site).where(Site.tenant_id != TEST_TENANT_ID))
        return len(result.scalars().all())


if __name__ == "__main__":
    asyncio.run(seed())
