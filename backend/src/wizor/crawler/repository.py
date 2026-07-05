"""Persistence-слой crawler: маппинг Pydantic ``CrawlResult`` → строка БД.

Единственное место, где DTO-шов (:mod:`wizor.crawler.schemas`) превращается в ORM
(:class:`wizor.crawler.models.CrawlResultRow`). Всегда tenant-scoped: ``tenant_id``
приходит из контекста вызова (Celery-задача берёт его из аргумента, эндпоинт — из
``request.state``), а не из тела DTO — источник истины по тенанту вне домена краула (§6.8).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from wizor.crawler.models import CrawlResultRow
from wizor.crawler.schemas import CrawlResult


async def save_crawl_result(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    result: CrawlResult,
) -> CrawlResultRow:
    """Сохранить результат краула, привязав его к тенанту и сайту.

    JSONB-поля сериализуются из Pydantic через ``model_dump(mode="json")`` —
    datetime/enum становятся JSON-совместимыми. Коммит — на вызывающей стороне
    (unit-of-work держит транзакцию), здесь только ``add`` + ``flush`` для получения PK.
    """
    row = CrawlResultRow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        site_id=site_id,
        crawled_at=result.crawled_at,
        pages_json=[page.model_dump(mode="json") for page in result.pages],
        audit_summary_json=[factor.model_dump(mode="json") for factor in result.audit_summary],
        schema_validation_json=result.schema_validation.model_dump(mode="json"),
        read_only_confirmed=result.read_only_confirmed,
    )
    session.add(row)
    await session.flush()
    return row
