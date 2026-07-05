"""crawl_results: read-only аудит сайта (P2, tenant-scoped, JSONB-поля)

Revision ID: 0002_crawl_results
Revises: 0001_initial
Create Date: 2026-07-05

Greenfield CREATE таблицы ``crawl_results`` (Refs: P2, ADR-0011). Несёт ``tenant_id``
(§6.8) с FK+index; ``site_id`` FK → ``sites.id``. Оба FK ``ON DELETE CASCADE``.
Структурированный аудит — в JSONB (форма = Pydantic ``CrawlResult``). Стиль DDL
повторяет 0001_initial (без f-string DDL-циклов, tripwire-friendly).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_crawl_results"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "crawl_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pages_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audit_summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "schema_validation_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("read_only_confirmed", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_crawl_results"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_crawl_results_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_crawl_results_site"
        ),
    )
    op.create_index("ix_crawl_results_tenant_id", "crawl_results", ["tenant_id"])
    op.create_index("ix_crawl_results_site_id", "crawl_results", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_crawl_results_site_id", table_name="crawl_results")
    op.drop_index("ix_crawl_results_tenant_id", table_name="crawl_results")
    op.drop_table("crawl_results")
