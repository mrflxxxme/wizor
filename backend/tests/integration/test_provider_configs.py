"""Integration: persist + tenant-изоляция ``provider_configs`` (P4, §6.8).

Помечены ``integration`` — реальный Postgres в CI (services). Предусловие (как в
test_db_smoke): ``alembic upgrade head`` + ``python -m wizor.iam.seed``. Проверяем, что
репозиторий upsert'ит routing-оверрайд tenant-scoped (повторный upsert не плодит строк,
а лишь переключает ``enabled``) и что запрос под чужим тенантом не возвращает строку
тестового тенанта (cross-tenant → 0 строк). Зеркалит P3 test_score_results.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select, text

from wizor.db.session import get_sessionmaker
from wizor.iam.seed import TEST_TENANT_ID
from wizor.llm_router.models import ProviderConfigRow
from wizor.llm_router.repository import load_provider_configs, upsert_provider_config

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_upsert_provider_config_is_idempotent() -> None:
    """Upsert по (tenant, task_type, provider) не плодит строк, переключает ``enabled``."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        first = await upsert_provider_config(
            session,
            tenant_id=TEST_TENANT_ID,
            task_type="content_gen",
            provider="openai",
            enabled=True,
        )
        await session.commit()
        assert first.enabled is True

    try:
        async with sessionmaker() as session:
            # Повторный upsert того же ключа → та же строка, enabled переключён.
            await upsert_provider_config(
                session,
                tenant_id=TEST_TENANT_ID,
                task_type="content_gen",
                provider="openai",
                enabled=False,
            )
            await session.commit()

        async with sessionmaker() as session:
            count = await session.execute(
                select(func.count())
                .select_from(ProviderConfigRow)
                .where(
                    ProviderConfigRow.tenant_id == TEST_TENANT_ID,
                    ProviderConfigRow.task_type == "content_gen",
                    ProviderConfigRow.provider == "openai",
                )
            )
            assert count.scalar_one() == 1

            configs = await load_provider_configs(
                session, tenant_id=TEST_TENANT_ID, task_type="content_gen"
            )
            openai_cfg = next(c for c in configs if c.provider == "openai")
            assert openai_cfg.enabled is False
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text(
                    "DELETE FROM provider_configs "
                    "WHERE tenant_id = :tid AND task_type = 'content_gen' AND provider = 'openai'"
                ),
                {"tid": str(TEST_TENANT_ID)},
            )
            await session.commit()


@pytest.mark.asyncio
async def test_tenant_isolation_provider_configs() -> None:
    """Cross-tenant → 0 строк: оверрайд чужого тенанта невидим под фильтром TEST-тенанта.

    Вставляем чужой тенант + его provider_config и свой config для TEST. Затем: (1)
    scoped-load по TEST не содержит чужую строку; (2) `WHERE tenant_id != TEST` не
    возвращает строку TEST-тенанта. Убираем за собой (чужой тенант — каскадом).
    """
    other_tenant = uuid.uuid4()
    sessionmaker = get_sessionmaker()

    async with sessionmaker() as session:
        await session.execute(
            text(
                "INSERT INTO tenants (id, name, slug, created_at, updated_at) "
                "VALUES (:id, :name, :slug, now(), now())"
            ),
            {"id": str(other_tenant), "name": "Other", "slug": f"other-{other_tenant}"},
        )
        await upsert_provider_config(
            session, tenant_id=other_tenant, task_type="batch", provider="vllm", enabled=True
        )
        await upsert_provider_config(
            session, tenant_id=TEST_TENANT_ID, task_type="batch", provider="vllm", enabled=True
        )
        # id собственной строки — для проверки, что чужой фильтр её не захватывает.
        own_id = (
            await session.execute(
                select(ProviderConfigRow.id).where(
                    ProviderConfigRow.tenant_id == TEST_TENANT_ID,
                    ProviderConfigRow.task_type == "batch",
                    ProviderConfigRow.provider == "vllm",
                )
            )
        ).scalar_one()
        await session.commit()

    try:
        async with sessionmaker() as session:
            # (1) scoped-load TEST не содержит чужого тенанта.
            scoped_tenants = {
                c.tenant_id for c in await load_provider_configs(session, tenant_id=TEST_TENANT_ID)
            }
            assert str(other_tenant) not in scoped_tenants

            # (2) scoped-load чужого тенанта не содержит TEST-тенанта.
            other_tenants = {
                c.tenant_id for c in await load_provider_configs(session, tenant_id=other_tenant)
            }
            assert str(TEST_TENANT_ID) not in other_tenants

            # (3) Cross-tenant: под фильтром «не TEST-тенант» собственной строки нет (0 строк).
            foreign = await session.execute(
                select(func.count())
                .select_from(ProviderConfigRow)
                .where(
                    ProviderConfigRow.tenant_id != TEST_TENANT_ID,
                    ProviderConfigRow.id == own_id,
                )
            )
            assert foreign.scalar_one() == 0
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text(
                    "DELETE FROM provider_configs "
                    "WHERE tenant_id = :tid AND task_type = 'batch' AND provider = 'vllm'"
                ),
                {"tid": str(TEST_TENANT_ID)},
            )
            # Чужой тенант удаляем каскадом (унесёт его provider_configs).
            await session.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": str(other_tenant)}
            )
            await session.commit()
