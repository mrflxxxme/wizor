"""ORM-модель ``crawl_results`` — persistence read-only аудита сайта (P2).

Одна таблица на результат краула. Несёт ``tenant_id`` через :class:`TenantMixin`
(инвариант §6.8) и FK на ``sites``. Структурированные поля аудита (страницы,
вердикты факторов, валидация JSON-LD) хранятся как JSONB — форма задаётся
Pydantic-DTO :class:`wizor.crawler.schemas.CrawlResult` (единственная граница типов).

ORM-класс назван ``CrawlResultRow``, чтобы не путать с Pydantic ``CrawlResult``.
Строка иммутабельна (краул — событие), поэтому только ``created_at`` без ``updated_at``.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKeyConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from wizor.db.base import Base, TenantMixin


class CrawlResultRow(Base, TenantMixin):
    """Строка ``crawl_results``: результат одного read-only краула сайта.

    ``tenant_id`` (из :class:`TenantMixin`) + FK на ``tenants`` дают изоляцию (§6.8);
    ``site_id`` привязывает результат к аудитируемому сайту. Оба FK — ``ON DELETE
    CASCADE`` (удаление тенанта/сайта уносит его крауллы).
    """

    __tablename__ = "crawl_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_crawl_results_tenant"
        ),
        ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_crawl_results_site"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    site_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    crawled_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pages_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    audit_summary_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    schema_validation_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    read_only_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
