"""Persistence-слой metrics: запись и чтение агрегата Visibility (P5).

Единственное место, где DTO-шов (:mod:`wizor.metrics.schemas`) превращается в ORM
(:class:`wizor.metrics.models.VisibilityMetricRow`) и обратно. Всегда tenant-scoped:
``tenant_id`` приходит из контекста вызова (эндпоинт — из ``request.state``, задача — из
аргумента), а НЕ из тела DTO (§6.8). Момент расчёта ``calculated_at`` инъектируется на
границе (часы вне чистого движка, детерминизм).
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.metrics.models import VisibilityMetricRow
from wizor.metrics.schemas import VisibilityComponents, VisibilityMetrics


def _to_metrics_dto(row: VisibilityMetricRow) -> VisibilityMetrics:
    """Спроецировать ORM-строку агрегата на DTO-шов (граница типов на выходе)."""
    return VisibilityMetrics(
        visibility_score=row.visibility_score,
        components=VisibilityComponents.model_validate(row.components),
        ci_lower=row.ci_lower,
        ci_upper=row.ci_upper,
        n=row.n,
        prompt_set_version=row.prompt_set_version,
    )


async def save_visibility_metrics(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    metrics: VisibilityMetrics,
    calculated_at: datetime.datetime,
) -> VisibilityMetricRow:
    """Сохранить агрегат Visibility, привязав его к тенанту и сайту (§6.8).

    ``components`` сериализуется из Pydantic через ``model_dump(mode="json")``.
    ``calculated_at`` инъектируется вызывающей стороной (движок остаётся чистым). Коммит —
    на вызывающей стороне; здесь ``add`` + ``flush`` для получения PK.
    """
    row = VisibilityMetricRow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        site_id=site_id,
        prompt_set_version=metrics.prompt_set_version,
        visibility_score=metrics.visibility_score,
        components=metrics.components.model_dump(mode="json"),
        ci_lower=metrics.ci_lower,
        ci_upper=metrics.ci_upper,
        n=metrics.n,
        calculated_at=calculated_at,
    )
    session.add(row)
    await session.flush()
    return row


async def load_latest_visibility(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
) -> VisibilityMetrics | None:
    """Загрузить самый свежий агрегат Visibility сайта (tenant-scoped, §6.8).

    Источник — последний по ``calculated_at``. Нет агрегата для (tenant, site) → ``None``
    (эндпоинт трактует как 404: probe ещё не считался).
    """
    stmt = (
        select(VisibilityMetricRow)
        .where(
            VisibilityMetricRow.tenant_id == tenant_id,
            VisibilityMetricRow.site_id == site_id,
        )
        .order_by(VisibilityMetricRow.calculated_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.scalars().first()
    return _to_metrics_dto(row) if row is not None else None
