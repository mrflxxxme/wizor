"""ORM-модель ``provider_configs`` — persistence routing-оверрайдов тенанта (P4).

Одна строка = правило включения/маршрутизации одного провайдера для одного
``task_type`` тенанта. Несёт ``tenant_id`` через :class:`TenantMixin` (инвариант §6.8)
и FK на ``tenants``. Форма поля задаётся Pydantic-DTO
:class:`wizor.llm_router.schemas.ProviderConfigDTO` (единственная граница типов).

ORM-класс назван ``ProviderConfigRow``, чтобы не путать с Pydantic ``ProviderConfigDTO``.
Уникальность ``(tenant_id, task_type, provider)`` гарантирует не более одной записи на
провайдера в рамках задачи тенанта (upsert по этому ключу — см. repository).
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from wizor.db.base import Base, TenantMixin


class ProviderConfigRow(Base, TenantMixin):
    """Строка ``provider_configs``: routing-оверрайд провайдера для тенанта (§6.8).

    ``tenant_id`` (из :class:`TenantMixin`) + FK на ``tenants`` дают изоляцию;
    ``(tenant_id, task_type, provider)`` уникальна. ``task_type`` и ``provider`` хранятся
    строками (значения — из ``Literal`` в :mod:`wizor.llm_router.schemas`); валидация формы
    остаётся за Pydantic-DTO на границе API.
    """

    __tablename__ = "provider_configs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_provider_configs_tenant"
        ),
        UniqueConstraint(
            "tenant_id", "task_type", "provider", name="uq_provider_configs_tenant_task_provider"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
