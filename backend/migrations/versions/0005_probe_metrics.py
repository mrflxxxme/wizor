"""probe_runs + prompt_sets + visibility_metrics: probe-мониторинг и Visibility (P5)

Revision ID: 0005_probe_metrics
Revises: 0004_provider_configs
Create Date: 2026-07-05

Greenfield CREATE трёх таблиц контекстов ``probe`` и ``metrics`` (Refs: P5). Все несут
``tenant_id`` (§6.8) с FK+index на ``tenants.id`` (``ON DELETE CASCADE``) и FK на
``sites.id``:

* ``probe_runs`` — сырой прогон промпта на модели (N≥5 на промпт×модель, FR-2.3).
* ``prompt_sets`` — версионируемый набор промптов; ``(tenant_id, site_id, version)``
  уникальна (правка → новая версия, AC-5).
* ``visibility_metrics`` — агрегат Visibility (4 компонента JSONB + полоса шума CI, AC-4).

Стиль DDL повторяет 0003/0004 (self-contained, без импорта app-кода, без f-string DDL).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_probe_metrics"
down_revision: str | None = "0004_provider_configs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "probe_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_id", sa.String(length=128), nullable=False),
        sa.Column("model", sa.String(length=32), nullable=False),
        sa.Column("run_index", sa.Integer(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("mentioned", sa.Boolean(), nullable=False),
        sa.Column("cited", sa.Boolean(), nullable=False),
        sa.Column("egress", sa.String(length=16), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_probe_runs"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_probe_runs_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_probe_runs_site"
        ),
    )
    op.create_index("ix_probe_runs_tenant_id", "probe_runs", ["tenant_id"])
    op.create_index("ix_probe_runs_site_id", "probe_runs", ["site_id"])

    op.create_table(
        "prompt_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("prompts", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prompt_sets"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_prompt_sets_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_prompt_sets_site"
        ),
        sa.UniqueConstraint(
            "tenant_id", "site_id", "version", name="uq_prompt_sets_tenant_site_version"
        ),
    )
    op.create_index("ix_prompt_sets_tenant_id", "prompt_sets", ["tenant_id"])
    op.create_index("ix_prompt_sets_site_id", "prompt_sets", ["site_id"])

    op.create_table(
        "visibility_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt_set_version", sa.Integer(), nullable=True),
        sa.Column("visibility_score", sa.Float(), nullable=False),
        sa.Column("components", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ci_lower", sa.Float(), nullable=False),
        sa.Column("ci_upper", sa.Float(), nullable=False),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_visibility_metrics"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_visibility_metrics_tenant"
        ),
        sa.ForeignKeyConstraint(
            ["site_id"], ["sites.id"], ondelete="CASCADE", name="fk_visibility_metrics_site"
        ),
    )
    op.create_index("ix_visibility_metrics_tenant_id", "visibility_metrics", ["tenant_id"])
    op.create_index("ix_visibility_metrics_site_id", "visibility_metrics", ["site_id"])


def downgrade() -> None:
    op.drop_index("ix_visibility_metrics_site_id", table_name="visibility_metrics")
    op.drop_index("ix_visibility_metrics_tenant_id", table_name="visibility_metrics")
    op.drop_table("visibility_metrics")
    op.drop_index("ix_prompt_sets_site_id", table_name="prompt_sets")
    op.drop_index("ix_prompt_sets_tenant_id", table_name="prompt_sets")
    op.drop_table("prompt_sets")
    op.drop_index("ix_probe_runs_site_id", table_name="probe_runs")
    op.drop_index("ix_probe_runs_tenant_id", table_name="probe_runs")
    op.drop_table("probe_runs")
