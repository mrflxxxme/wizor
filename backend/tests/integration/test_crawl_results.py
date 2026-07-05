"""Integration: persist + tenant-изоляция ``crawl_results`` (AC-5).

Помечены ``integration`` — реальный Postgres в CI (services). Предусловие (как в
test_db_smoke): ``alembic upgrade head`` + ``python -m wizor.iam.seed``. Проверяем,
что репозиторий пишет строку tenant-scoped и что запрос `WHERE tenant_id != <test>`
не возвращает данные тестового тенанта (§6.8, AC-5).
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from sqlalchemy import func, select, text

from wizor.crawler.models import CrawlResultRow
from wizor.crawler.repository import save_crawl_result
from wizor.crawler.schemas import (
    CrawlResult,
    FactorVerdict,
    PageAudit,
    SchemaValidation,
)
from wizor.db.session import get_sessionmaker
from wizor.iam.seed import TEST_SITE_ID, TEST_TENANT_ID

pytestmark = pytest.mark.integration


def _sample_result() -> CrawlResult:
    """Минимальный валидный ``CrawlResult`` для persist-проверки."""
    return CrawlResult(
        site_url="https://example.test",
        crawled_at=datetime.datetime.now(tz=datetime.UTC),
        pages=[
            PageAudit(
                url="https://example.test/",
                http_status=200,
                content_hash="deadbeef",
                rendered_via_js=False,
                signals={"h1": ["Заголовок"]},
            )
        ],
        audit_summary=[
            FactorVerdict(factor="robots_txt", verdict="pass", detail="robots.txt найден")
        ],
        schema_validation=SchemaValidation(schema_valid=True, types_found=["Organization"]),
        read_only_confirmed=True,
    )


@pytest.mark.asyncio
async def test_save_crawl_result_persists_row() -> None:
    """Репозиторий сохраняет строку для тестового тенанта; JSONB-поля заполнены."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        row = await save_crawl_result(
            session,
            tenant_id=TEST_TENANT_ID,
            site_id=TEST_SITE_ID,
            result=_sample_result(),
        )
        await session.commit()
        row_id = row.id

    try:
        async with sessionmaker() as session:
            fetched = await session.get(CrawlResultRow, row_id)
            assert fetched is not None
            assert fetched.tenant_id == TEST_TENANT_ID
            assert fetched.site_id == TEST_SITE_ID
            assert fetched.read_only_confirmed is True
            assert fetched.audit_summary_json[0]["factor"] == "robots_txt"
            assert fetched.schema_validation_json["schema_valid"] is True
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text("DELETE FROM crawl_results WHERE id = :id"), {"id": str(row_id)}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_tenant_isolation_ac5() -> None:
    """AC-5: строка чужого тенанта не видна под фильтром тестового тенанта.

    Вставляем чужой тенант+сайт+crawl_result, свой crawl_result — для TEST. Затем:
    (1) scoped-запрос по TEST не содержит чужую строку; (2) `WHERE tenant_id != TEST`
    не возвращает ни одной строки TEST-тенанта. Убираем за собой (cascade).
    """
    other_tenant = uuid.uuid4()
    other_site = uuid.uuid4()
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
        other_row = await save_crawl_result(
            session, tenant_id=other_tenant, site_id=other_site, result=_sample_result()
        )
        own_row = await save_crawl_result(
            session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID, result=_sample_result()
        )
        await session.commit()
        own_id, other_id = own_row.id, other_row.id

    try:
        async with sessionmaker() as session:
            scoped = await session.execute(
                select(CrawlResultRow).where(CrawlResultRow.tenant_id == TEST_TENANT_ID)
            )
            scoped_ids = {r.id for r in scoped.scalars().all()}
            assert own_id in scoped_ids
            assert other_id not in scoped_ids

            # AC-5: под фильтром «не тестовый тенант» строк TEST-тенанта нет.
            foreign = await session.execute(
                select(func.count())
                .select_from(CrawlResultRow)
                .where(
                    CrawlResultRow.tenant_id != TEST_TENANT_ID,
                    CrawlResultRow.id == own_id,
                )
            )
            assert foreign.scalar_one() == 0
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text("DELETE FROM crawl_results WHERE id = :id"), {"id": str(own_id)}
            )
            # Чужой тенант удаляем каскадом (унесёт его site + crawl_result).
            await session.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": str(other_tenant)}
            )
            await session.commit()
