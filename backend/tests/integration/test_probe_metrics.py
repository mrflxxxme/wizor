"""Integration: persist + tenant-изоляция probe_runs / visibility_metrics + версии (P5).

Помечены ``integration`` — реальный Postgres в CI (services). Предусловие (как в
test_db_smoke): ``alembic upgrade head`` + ``python -m wizor.iam.seed``. Проверяем, что
репозитории пишут прогоны и агрегат tenant-scoped, что чужой тенант их не видит (§6.8) и
что правка набора промптов создаёт новую версию (AC-5). Зеркалит P3 test_score_results.
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from sqlalchemy import func, select, text

from wizor.db.session import get_sessionmaker
from wizor.iam.seed import TEST_SITE_ID, TEST_TENANT_ID
from wizor.metrics.models import VisibilityMetricRow
from wizor.metrics.repository import load_latest_visibility, save_visibility_metrics
from wizor.metrics.schemas import VisibilityComponents, VisibilityMetrics
from wizor.probe.models import ProbeRunRow
from wizor.probe.repository import (
    load_active_prompt_set,
    save_probe_runs,
    upsert_prompt_set,
)
from wizor.probe.schemas import ProbeRun

pytestmark = pytest.mark.integration


def _sample_runs(n: int = 5) -> list[ProbeRun]:
    now = datetime.datetime.now(tz=datetime.UTC)
    return [
        ProbeRun(
            prompt_id="0",
            model="alice_yandex",
            run_index=i,
            raw_response="response",
            mentioned=True,
            cited=(i == 0),
            egress="ru",
            run_at=now,
            error=None,
        )
        for i in range(n)
    ]


def _sample_metrics() -> VisibilityMetrics:
    return VisibilityMetrics(
        visibility_score=80.0,
        components=VisibilityComponents(coverage=1.0, sov=1.0, citation_rate=0.2, stability=1.0),
        ci_lower=78.0,
        ci_upper=82.0,
        n=5,
        prompt_set_version=1,
    )


async def _cleanup_test_rows() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        for table in ("probe_runs", "visibility_metrics", "prompt_sets"):
            await session.execute(
                text(f"DELETE FROM {table} WHERE tenant_id = :tid AND site_id = :sid"),  # noqa: S608
                {"tid": str(TEST_TENANT_ID), "sid": str(TEST_SITE_ID)},
            )
        await session.commit()


@pytest.mark.asyncio
async def test_probe_and_visibility_persist_and_read() -> None:
    """Репозитории пишут прогоны + агрегат tenant-scoped; чтение возвращает их обратно."""
    now = datetime.datetime.now(tz=datetime.UTC)
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        rows = await save_probe_runs(
            session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID, runs=_sample_runs()
        )
        await save_visibility_metrics(
            session,
            tenant_id=TEST_TENANT_ID,
            site_id=TEST_SITE_ID,
            metrics=_sample_metrics(),
            calculated_at=now,
        )
        await session.commit()
        assert len(rows) == 5

    try:
        async with sessionmaker() as session:
            fetched = await load_latest_visibility(
                session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID
            )
            assert fetched is not None
            assert fetched.visibility_score == 80.0
            assert fetched.components.coverage == 1.0
            assert fetched.prompt_set_version == 1

            run_count = await session.execute(
                select(func.count())
                .select_from(ProbeRunRow)
                .where(
                    ProbeRunRow.tenant_id == TEST_TENANT_ID,
                    ProbeRunRow.site_id == TEST_SITE_ID,
                )
            )
            assert run_count.scalar_one() == 5
    finally:
        await _cleanup_test_rows()


@pytest.mark.asyncio
async def test_tenant_isolation_probe_and_metrics() -> None:
    """§6.8: прогоны и агрегат чужого тенанта не видны под фильтром тестового тенанта."""
    other_tenant = uuid.uuid4()
    other_site = uuid.uuid4()
    now = datetime.datetime.now(tz=datetime.UTC)
    sessionmaker = get_sessionmaker()

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
            {"id": str(other_site), "tid": str(other_tenant), "url": "https://other.test"},
        )
        await save_probe_runs(
            session, tenant_id=other_tenant, site_id=other_site, runs=_sample_runs()
        )
        await save_visibility_metrics(
            session,
            tenant_id=other_tenant,
            site_id=other_site,
            metrics=_sample_metrics(),
            calculated_at=now,
        )
        own_metric = await save_visibility_metrics(
            session,
            tenant_id=TEST_TENANT_ID,
            site_id=TEST_SITE_ID,
            metrics=_sample_metrics(),
            calculated_at=now,
        )
        await session.commit()
        own_id = own_metric.id

    try:
        async with sessionmaker() as session:
            # scoped-запрос по TEST не содержит строк чужого тенанта.
            scoped = await session.execute(
                select(VisibilityMetricRow).where(VisibilityMetricRow.tenant_id == TEST_TENANT_ID)
            )
            scoped_tenants = {r.tenant_id for r in scoped.scalars().all()}
            assert other_tenant not in scoped_tenants

            # Под фильтром «не тестовый тенант» собственной строки нет (0 строк).
            foreign = await session.execute(
                select(func.count())
                .select_from(VisibilityMetricRow)
                .where(
                    VisibilityMetricRow.tenant_id != TEST_TENANT_ID,
                    VisibilityMetricRow.id == own_id,
                )
            )
            assert foreign.scalar_one() == 0

            # probe_runs чужого тенанта невидимы под фильтром TEST-тенанта.
            own_runs = await session.execute(
                select(func.count())
                .select_from(ProbeRunRow)
                .where(
                    ProbeRunRow.tenant_id == TEST_TENANT_ID,
                    ProbeRunRow.site_id == TEST_SITE_ID,
                )
            )
            assert own_runs.scalar_one() == 5
    finally:
        await _cleanup_test_rows()
        async with sessionmaker() as session:
            # Чужой тенант удаляем каскадом (унесёт его site + probe_runs + метрики).
            await session.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": str(other_tenant)}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_prompt_set_versioning_ac5() -> None:
    """AC-5: правка набора промптов создаёт новую версию; активный = последняя версия."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        first = await upsert_prompt_set(
            session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID, prompts=["a", "b"]
        )
        await session.commit()

    try:
        async with sessionmaker() as session:
            second = await upsert_prompt_set(
                session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID, prompts=["a", "b", "c"]
            )
            await session.commit()
        assert second.version == first.version + 1

        async with sessionmaker() as session:
            active = await load_active_prompt_set(
                session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID
            )
            assert active is not None
            assert active.version == second.version
            assert active.prompts == ["a", "b", "c"]
    finally:
        await _cleanup_test_rows()
