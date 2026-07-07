"""Persistence-слой probe: запись прогонов + версионируемые наборы промптов (P5).

Единственное место, где DTO-шов (:mod:`wizor.probe.schemas`) превращается в ORM
(:mod:`wizor.probe.models`). Всегда tenant-scoped: ``tenant_id`` приходит из контекста
вызова (эндпоинт — из ``request.state``, задача — из аргумента), а НЕ из тела DTO (§6.8).

Даёт probe-каналу три примитива: сохранить N сырых прогонов, загрузить активный набор
промптов (последняя версия) и создать новую версию набора (AC-5: правка → новая версия,
старые probe остаются привязаны к своей версии).
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.probe.models import ProbeRunRow, PromptSetRow
from wizor.probe.schemas import ProbeRun, PromptSetDTO


def _to_prompt_set_dto(row: PromptSetRow) -> PromptSetDTO:
    """Спроецировать ORM-строку набора промптов на DTO-шов (граница типов на выходе)."""
    return PromptSetDTO(
        id=str(row.id),
        site_id=str(row.site_id),
        version=row.version,
        prompts=list(row.prompts),
    )


async def save_probe_runs(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    runs: Sequence[ProbeRun],
) -> list[ProbeRunRow]:
    """Сохранить N сырых probe-прогонов (tenant-scoped, §6.8). Коммит — на вызывающей стороне.

    Каждый ``ProbeRun`` (включая упавший — с ``error``) материализуется в строку: полное
    распределение хранится для CI (§6.7) и evidence P8. ``flush`` — чтобы получить PK.
    """
    rows = [
        ProbeRunRow(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            site_id=site_id,
            prompt_id=run.prompt_id,
            model=run.model,
            run_index=run.run_index,
            raw_response=run.raw_response,
            mentioned=run.mentioned,
            cited=run.cited,
            egress=run.egress,
            run_at=run.run_at,
            error=run.error,
        )
        for run in runs
    ]
    session.add_all(rows)
    await session.flush()
    return rows


async def load_active_prompt_set(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
) -> PromptSetDTO | None:
    """Загрузить активный (последняя версия) набор промптов сайта (tenant-scoped, §6.8).

    Нет набора для (tenant, site) → ``None`` (probe-задача трактует как «нечего прогонять»,
    эндпоинт — как 404).
    """
    stmt = (
        select(PromptSetRow)
        .where(PromptSetRow.tenant_id == tenant_id, PromptSetRow.site_id == site_id)
        .order_by(PromptSetRow.version.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.scalars().first()
    return _to_prompt_set_dto(row) if row is not None else None


async def upsert_prompt_set(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    site_id: uuid.UUID,
    prompts: list[str],
) -> PromptSetDTO:
    """Создать НОВУЮ версию набора промптов сайта (AC-5: правка не перезатирает старую).

    Новая версия = ``max(version) + 1`` для (tenant, site) или 1, если набора ещё нет.
    Исторические ``probe_runs`` остаются валидны относительно своих версий. ``tenant_id`` —
    из контекста вызова, НЕ из тела (§6.8). Коммит — на вызывающей стороне.
    """
    max_version = (
        await session.execute(
            select(func.max(PromptSetRow.version)).where(
                PromptSetRow.tenant_id == tenant_id, PromptSetRow.site_id == site_id
            )
        )
    ).scalar_one_or_none()
    next_version = (max_version or 0) + 1

    row = PromptSetRow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        site_id=site_id,
        version=next_version,
        prompts=list(prompts),
    )
    session.add(row)
    await session.flush()
    return _to_prompt_set_dto(row)
