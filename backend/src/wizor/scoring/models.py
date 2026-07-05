"""ORM-модель ``score_results`` — persistence AI-Readiness Score (P3, T3).

Одна строка на расчёт Score. Несёт ``tenant_id`` через :class:`TenantMixin`
(инвариант §6.8) и FK на ``sites``. Раскрытые компоненты и Readiness-проекция хранятся
как JSONB — форма задаётся Pydantic-DTO :mod:`wizor.scoring.schemas` (единственная
граница типов). Строка иммутабельна (расчёт — событие), поэтому только ``created_at``.

ORM-класс назван ``ScoreResultRow``, чтобы не путать с Pydantic ``ScoreResult``.

``embedding`` — НУЛЛАБЕЛЬНЫЙ стаб-вектор под будущий semantic search (NFR-6). Колонка
типа ``vector(N)`` (расширение pgvector активировано в 0001_initial); в P3 НЕ
вычисляется и всегда ``NULL`` — задел под P-фазу semantic search, не рабочий индекс.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any, Final

from sqlalchemy import DateTime, Float, ForeignKeyConstraint, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from wizor.db.base import Base, TenantMixin

EMBEDDING_DIM: Final = 1536
"""Размерность стаб-вектора эмбеддинга (провизорно; фактический источник — P-фаза
semantic search, NFR-6). В P3 колонка всегда NULL — эмбеддинги не вычисляются."""


class Vector(UserDefinedType[list[float]]):
    """Минимальный тип-обёртка pgvector ``vector(dim)`` (без зависимости от pgvector-пакета).

    Достаточен для DDL стаб-колонки: рендерит ``vector(dim)`` и биндит ``NULL`` как есть
    (эмбеддинги в P3 не пишутся). Полноценный тип (операторы расстояния, индексы ivfflat/
    hnsw) подключается в P-фазе semantic search вместе с реальными эмбеддингами.
    """

    cache_ok = True

    def __init__(self, dim: int) -> None:
        """Зафиксировать размерность вектора для DDL ``vector(dim)``."""
        super().__init__()
        self.dim = dim

    def get_col_spec(self, **_kw: Any) -> str:
        """DDL-спецификация колонки ``vector(<dim>)`` (сигнатура базового типа)."""
        return f"vector({self.dim})"


class ScoreResultRow(Base, TenantMixin):
    """Строка ``score_results``: один детерминированный расчёт Score для сайта.

    ``tenant_id`` (из :class:`TenantMixin`) + FK на ``tenants`` дают изоляцию (§6.8);
    ``site_id`` привязывает результат к сайту. Оба FK — ``ON DELETE CASCADE``.
    """

    __tablename__ = "score_results"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_score_results_tenant"
        ),
        ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_score_results_site"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    site_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_version: Mapped[str] = mapped_column(String(32), nullable=False)
    components_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    projection_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False)
    calculated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Стаб semantic-search (NFR-6): всегда NULL в P3, эмбеддинги не вычисляются.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
