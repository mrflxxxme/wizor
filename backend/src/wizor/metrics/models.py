"""ORM-модель ``visibility_metrics`` — persistence агрегата Visibility (P5).

Одна строка = один расчёт Visibility по сайту (агрегат probe-прогонов активной версии
набора промптов). Несёт ``tenant_id`` через :class:`TenantMixin` (инвариант §6.8) и FK на
``sites``. 4 компонента (coverage/sov/citation_rate/stability) хранятся как JSONB — форма
задаётся Pydantic-DTO :class:`wizor.metrics.schemas.VisibilityComponents`. ``ci_lower``/
``ci_upper`` несут полосу шума (§6.2/§6.7 honest-forecast: диапазон, не гарантия); ``n`` —
число прогонов в основе (N≥5 для заявляемого CI). Строка иммутабельна (расчёт — событие),
поэтому только ``created_at``; момент расчёта — ``calculated_at`` (инъектируется на границе).

ORM-класс назван ``VisibilityMetricRow``, чтобы не путать с Pydantic ``VisibilityMetrics``.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Float, ForeignKeyConstraint, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from wizor.db.base import Base, TenantMixin


class VisibilityMetricRow(Base, TenantMixin):
    """Строка ``visibility_metrics``: агрегат Visibility сайта (§6.8, AC-4).

    ``tenant_id`` (из :class:`TenantMixin`) + FK на ``tenants`` дают изоляцию; ``site_id``
    привязывает агрегат к сайту. Оба FK — ``ON DELETE CASCADE``. ``prompt_set_version``
    фиксирует версию набора промптов, по которой считался агрегат (AC-5); ``NULL`` —
    если версия неизвестна (напр. ad-hoc пересчёт).
    """

    __tablename__ = "visibility_metrics"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_visibility_metrics_tenant"
        ),
        ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_visibility_metrics_site"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    site_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    prompt_set_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    components: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    ci_lower: Mapped[float] = mapped_column(Float, nullable=False)
    ci_upper: Mapped[float] = mapped_column(Float, nullable=False)
    n: Mapped[int] = mapped_column(Integer, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
