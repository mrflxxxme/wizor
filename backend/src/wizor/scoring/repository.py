"""Persistence-слой scoring: чтение входа краула + запись результата Score (P3, T5).

Единственное место, где DTO-шов (:mod:`wizor.scoring.schemas`) превращается в ORM
(:class:`wizor.scoring.models.ScoreResultRow`), и где читается вход из соседнего
контекста (`crawler.crawl_results`). Всегда tenant-scoped: ``tenant_id`` приходит из
контекста вызова (эндпоинт — из ``request.state``), а НЕ из тела DTO (§6.8).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.crawler.models import CrawlResultRow
from wizor.iam.models import Site
from wizor.scoring.models import ScoreResultRow
from wizor.scoring.schemas import ScoreResult


async def load_latest_crawl(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
) -> CrawlResultRow | None:
    """Загрузить последний краул сайта строго в рамках тенанта (§6.8).

    Источник входа для Score — самый свежий `crawl_results` (по ``crawled_at``). Нет
    краула для (tenant, site) → ``None`` (эндпоинт трактует как 404: скорить нечего).
    """
    stmt = (
        select(CrawlResultRow)
        .where(
            CrawlResultRow.tenant_id == tenant_id,
            CrawlResultRow.site_id == site_id,
        )
        .order_by(CrawlResultRow.crawled_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalars().first()


async def load_site_url(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
) -> str | None:
    """Вернуть URL сайта (tenant-scoped) для наполнения `ScoreResult.site_url`. Нет → ``None``."""
    stmt = select(Site.url).where(Site.id == site_id, Site.tenant_id == tenant_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def save_score_result(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    result: ScoreResult,
) -> ScoreResultRow:
    """Сохранить результат Score, привязав его к тенанту и сайту.

    JSONB-поля сериализуются из Pydantic через ``model_dump(mode="json")``. ``embedding``
    остаётся ``NULL`` (стаб NFR-6, не вычисляется в P3). Коммит — на вызывающей стороне;
    здесь ``add`` + ``flush`` для получения PK.
    """
    row = ScoreResultRow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        site_id=site_id,
        score=result.score,
        score_version=result.score_version,
        components_json=[component.model_dump(mode="json") for component in result.components],
        projection_json=[projection.model_dump(mode="json") for projection in result.projection],
        calculated_at=result.calculated_at,
        embedding=None,
    )
    session.add(row)
    await session.flush()
    return row
