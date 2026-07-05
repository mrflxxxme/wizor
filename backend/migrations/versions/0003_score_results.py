"""score_results: детерминированный AI-Readiness Score (P3, tenant-scoped, JSONB + pgvector-стаб)

Revision ID: 0003_score_results
Revises: 0002_crawl_results
Create Date: 2026-07-05

Greenfield CREATE таблицы ``score_results`` (Refs: P3). Несёт ``tenant_id`` (§6.8) с
FK+index; ``site_id`` FK → ``sites.id``. Оба FK ``ON DELETE CASCADE``. Компоненты и
Readiness-проекция — в JSONB (форма = Pydantic ``ScoreResult``). ``embedding`` — нуллабельный
стаб ``vector(N)`` под будущий semantic search (NFR-6): расширение pgvector активировано в
0001_initial, здесь колонка НЕ заполняется. Стиль DDL повторяет 0002 (без f-string DDL-циклов).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_score_results"
down_revision: str | None = "0002_crawl_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class _VectorDDL(sa.types.UserDefinedType[object]):
    """Замороженный тип pgvector-колонки ДЛЯ ЭТОЙ миграции — self-contained, не зависит
    от app-кода (`wizor.scoring.models`). Миграция = неизменяемый снапшот истории:
    если ``EMBEDDING_DIM`` в приложении однажды изменится, DDL этой миграции не должен
    молча меняться. Размерность зафиксирована литералом (см. ревью P3).
    """

    cache_ok = True

    def get_col_spec(self, **_kw: object) -> str:
        return "vector(1536)"


def upgrade() -> None:
    op.create_table(
        "score_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("score_version", sa.String(length=32), nullable=False),
        sa.Column("components_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("projection_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        # Стаб semantic-search (NFR-6): всегда NULL в P3, pgvector-расширение из 0001.
        sa.Column("embedding", _VectorDDL(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_score_results"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_score_results_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_score_results_site"
        ),
    )
    op.create_index("ix_score_results_tenant_id", "score_results", ["tenant_id"])
    op.create_index("ix_score_results_site_id", "score_results", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_score_results_site_id", table_name="score_results")
    op.drop_index("ix_score_results_tenant_id", table_name="score_results")
    op.drop_table("score_results")
