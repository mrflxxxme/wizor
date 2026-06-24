"""Декларативная база и общие миксины (timestamps, tenant-scoping).

``TenantMixin`` материализует инвариант §6.8: каждая прикладная таблица несёт
``tenant_id`` и индекс по нему. Таблицы IAM наследуют его (см. iam/models.py).
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Корень декларативных моделей WIZOR."""


class TimestampMixin:
    """Серверные ``created_at`` / ``updated_at`` (UTC)."""

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    """Обязательный ``tenant_id`` для multi-tenant изоляции (§6.8).

    Внимание: наличие колонки — необходимое, но не достаточное условие изоляции.
    Каждый запрос ОБЯЗАН фильтроваться по ``tenant_id`` из контекста (core.tenancy).
    RLS-политики Postgres добавляются в P9 как defense-in-depth.
    """

    tenant_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
