"""ORM-модели контекста probe — persistence probe-прогонов и наборов промптов (P5).

Две таблицы, обе tenant-scoped через :class:`TenantMixin` (инвариант §6.8):

* ``probe_runs`` — один сырой прогон одного промпта на одной модели (N≥5 таких на
  промпт×модель, FR-2.3). Хранится полное распределение, а не только агрегат — основа
  для CI (§6.7) и evidence P8. Форма — Pydantic-шов :class:`wizor.probe.schemas.ProbeRun`.
* ``prompt_sets`` — версионируемый набор промптов сайта (FR-2.1, AC-5). Уникальность
  ``(tenant_id, site_id, version)`` гарантирует, что новая версия не перезатирает старую;
  исторические probe остаются привязанными к своей версии.

ORM-классы названы ``…Row``, чтобы не путать с Pydantic-DTO (``ProbeRun``/``PromptSetDTO``).
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from wizor.db.base import Base, TenantMixin


class ProbeRunRow(Base, TenantMixin):
    """Строка ``probe_runs``: один сырой прогон промпта на модели (§6.8, FR-2.3).

    ``tenant_id`` (из :class:`TenantMixin`) + FK на ``tenants`` дают изоляцию; ``site_id``
    привязывает прогон к сайту. Оба FK — ``ON DELETE CASCADE``. ``model``/``egress`` —
    строки (значения из ``Literal`` в :mod:`wizor.probe.schemas`); валидация формы — за
    Pydantic-DTO на границе. ``error`` заполняется при сбое прогона (fault-isolation,
    AC-6) — прогон всё равно сохраняется, но исключается из успешных при агрегации.
    """

    __tablename__ = "probe_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_probe_runs_tenant"
        ),
        ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_probe_runs_site"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    site_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    prompt_id: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(32), nullable=False)
    run_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    mentioned: Mapped[bool] = mapped_column(Boolean, nullable=False)
    cited: Mapped[bool] = mapped_column(Boolean, nullable=False)
    egress: Mapped[str] = mapped_column(String(16), nullable=False)
    run_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PromptSetRow(Base, TenantMixin):
    """Строка ``prompt_sets``: версионируемый набор промптов сайта (§6.8, FR-2.1, AC-5).

    ``(tenant_id, site_id, version)`` уникальна — правка набора создаёт НОВУЮ версию, не
    перезатирая старую; исторические ``probe_runs`` остаются валидны относительно своей
    версии. ``prompts`` — JSONB-массив строк (форма — Pydantic ``PromptSetDTO.prompts``).
    """

    __tablename__ = "prompt_sets"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_prompt_sets_tenant"
        ),
        ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_prompt_sets_site"
        ),
        UniqueConstraint(
            "tenant_id", "site_id", "version", name="uq_prompt_sets_tenant_site_version"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    site_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompts: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
