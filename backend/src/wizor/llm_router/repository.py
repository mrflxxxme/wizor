"""Persistence-слой llm-router: routing-оверрайды провайдеров тенанта (P4).

Единственное место, где DTO-шов (:mod:`wizor.llm_router.schemas`) превращается в ORM
(:class:`wizor.llm_router.models.ProviderConfigRow`). Всегда tenant-scoped: ``tenant_id``
приходит из контекста вызова (эндпоинт — из ``request.state``), а НЕ из тела DTO (§6.8).

Даёт роутеру два примитива: загрузить оверрайды тенанта (какие провайдеры включены под
какой ``task_type``) и upsert одного правила (включить/выключить провайдера) по
уникальному ключу ``(tenant_id, task_type, provider)``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.llm_router.models import ProviderConfigRow
from wizor.llm_router.schemas import Provider, ProviderConfigDTO, TaskType


def _to_dto(row: ProviderConfigRow) -> ProviderConfigDTO:
    """Спроецировать ORM-строку на DTO-шов (граница типов на выходе репозитория)."""
    # task_type/provider хранятся строками; Pydantic-DTO валидирует их как Literal на входе.
    return ProviderConfigDTO(
        tenant_id=str(row.tenant_id),
        task_type=row.task_type,
        provider=row.provider,
        enabled=row.enabled,
    )


async def load_provider_configs(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    task_type: TaskType | None = None,
) -> list[ProviderConfigDTO]:
    """Загрузить routing-оверрайды тенанта (строго в рамках ``tenant_id``, §6.8).

    Без ``task_type`` → все правила тенанта; с ``task_type`` → только правила этой задачи
    (используется роутером при выборе провайдера). Порядок детерминирован (по ключу).
    """
    stmt = select(ProviderConfigRow).where(ProviderConfigRow.tenant_id == tenant_id)
    if task_type is not None:
        stmt = stmt.where(ProviderConfigRow.task_type == task_type)
    stmt = stmt.order_by(ProviderConfigRow.task_type, ProviderConfigRow.provider)
    result = await session.execute(stmt)
    return [_to_dto(row) for row in result.scalars().all()]


async def upsert_provider_config(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    task_type: TaskType,
    provider: Provider,
    enabled: bool,
) -> ProviderConfigDTO:
    """Включить/выключить провайдера тенанта под ``task_type`` (upsert по уникальному ключу).

    Конфликт по ``(tenant_id, task_type, provider)`` → обновляем только ``enabled`` (правило
    уже есть). ``tenant_id`` — из контекста вызова, НЕ из DTO (§6.8). Коммит — на вызывающей
    стороне; здесь ``flush`` для получения актуальной строки.
    """
    stmt = (
        pg_insert(ProviderConfigRow)
        .values(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            task_type=task_type,
            provider=provider,
            enabled=enabled,
        )
        .on_conflict_do_update(
            constraint="uq_provider_configs_tenant_task_provider",
            set_={"enabled": enabled},
        )
        .returning(ProviderConfigRow)
    )
    result = await session.execute(stmt)
    await session.flush()
    row = result.scalar_one()
    return _to_dto(row)
