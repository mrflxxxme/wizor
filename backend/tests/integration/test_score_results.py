"""Integration: persist + tenant-изоляция ``score_results`` (AC-6).

Помечены ``integration`` — реальный Postgres в CI (services). Предусловие (как в
test_db_smoke): ``alembic upgrade head`` + ``python -m wizor.iam.seed``. Проверяем, что
репозиторий пишет строку Score tenant-scoped и что запрос под чужим тенантом не
возвращает строку тестового тенанта (§6.8, AC-6). Зеркалит P2 test_crawl_results.
"""

from __future__ import annotations

import datetime
import uuid

import pytest
from sqlalchemy import func, select, text

from wizor.db.session import get_sessionmaker
from wizor.iam.seed import TEST_SITE_ID, TEST_TENANT_ID
from wizor.scoring.models import ScoreResultRow
from wizor.scoring.repository import save_score_result
from wizor.scoring.schemas import ScoreComponent, ScoreProjection, ScoreResult

pytestmark = pytest.mark.integration


def _sample_score_result() -> ScoreResult:
    """Минимальный валидный ``ScoreResult`` для persist-проверки."""
    return ScoreResult(
        site_url="https://example.test",
        score=63.6364,
        score_version="1.0.0",
        components=[
            ScoreComponent(
                name="robots_txt",
                layer="discovery",
                weight=12.0,
                value=1.0,
                verdict="pass",
                contribution=12.0,
                description="robots",
            )
        ],
        projection=[ScoreProjection(fix_id="fix_faq", delta_score=36.3636, new_score=100.0)],
        calculated_at=datetime.datetime.now(tz=datetime.UTC),
    )


@pytest.mark.asyncio
async def test_save_score_result_persists_row() -> None:
    """Репозиторий сохраняет строку для тестового тенанта; JSONB-поля заполнены."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        row = await save_score_result(
            session,
            tenant_id=TEST_TENANT_ID,
            site_id=TEST_SITE_ID,
            result=_sample_score_result(),
        )
        await session.commit()
        row_id = row.id

    try:
        async with sessionmaker() as session:
            fetched = await session.get(ScoreResultRow, row_id)
            assert fetched is not None
            assert fetched.tenant_id == TEST_TENANT_ID
            assert fetched.site_id == TEST_SITE_ID
            assert fetched.score == 63.6364
            assert fetched.score_version == "1.0.0"
            assert fetched.components_json[0]["name"] == "robots_txt"
            assert fetched.projection_json[0]["fix_id"] == "fix_faq"
            assert fetched.embedding is None  # стаб NFR-6: не вычисляется в P3
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text("DELETE FROM score_results WHERE id = :id"), {"id": str(row_id)}
            )
            await session.commit()


@pytest.mark.asyncio
async def test_tenant_isolation_ac6() -> None:
    """AC-6: строка Score чужого тенанта не видна под фильтром тестового тенанта.

    Вставляем чужой тенант+сайт+score_result и свой score_result для TEST. Затем:
    (1) scoped-запрос по TEST не содержит чужую строку; (2) `WHERE tenant_id != TEST`
    не возвращает строку TEST-тенанта. Убираем за собой (cascade).
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
        other_row = await save_score_result(
            session, tenant_id=other_tenant, site_id=other_site, result=_sample_score_result()
        )
        own_row = await save_score_result(
            session, tenant_id=TEST_TENANT_ID, site_id=TEST_SITE_ID, result=_sample_score_result()
        )
        await session.commit()
        own_id, other_id = own_row.id, other_row.id

    try:
        async with sessionmaker() as session:
            scoped = await session.execute(
                select(ScoreResultRow).where(ScoreResultRow.tenant_id == TEST_TENANT_ID)
            )
            scoped_ids = {r.id for r in scoped.scalars().all()}
            assert own_id in scoped_ids
            assert other_id not in scoped_ids

            # AC-6: под фильтром «не тестовый тенант» строк TEST-тенанта нет.
            foreign = await session.execute(
                select(func.count())
                .select_from(ScoreResultRow)
                .where(
                    ScoreResultRow.tenant_id != TEST_TENANT_ID,
                    ScoreResultRow.id == own_id,
                )
            )
            assert foreign.scalar_one() == 0
    finally:
        async with sessionmaker() as session:
            await session.execute(
                text("DELETE FROM score_results WHERE id = :id"), {"id": str(own_id)}
            )
            # Чужой тенант удаляем каскадом (унесёт его site + score_result).
            await session.execute(
                text("DELETE FROM tenants WHERE id = :id"), {"id": str(other_tenant)}
            )
            await session.commit()
