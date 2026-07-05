"""provider_configs: routing-оверрайды провайдеров тенанта (P4, tenant-scoped)

Revision ID: 0004_provider_configs
Revises: 0003_score_results
Create Date: 2026-07-05

Greenfield CREATE таблицы ``provider_configs`` (Refs: P4). Несёт ``tenant_id`` (§6.8) с
FK+index на ``tenants.id`` (``ON DELETE CASCADE``). Одна строка = правило включения одного
провайдера для одного ``task_type`` тенанта; ``(tenant_id, task_type, provider)`` уникальна
(upsert по этому ключу). ``task_type``/``provider`` — строки (значения из ``Literal`` в
schemas). Стиль DDL повторяет 0003 (self-contained, без импорта app-кода, без f-string DDL).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_provider_configs"
down_revision: str | None = "0003_score_results"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_provider_configs"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_provider_configs_tenant"
        ),
        sa.UniqueConstraint(
            "tenant_id", "task_type", "provider", name="uq_provider_configs_tenant_task_provider"
        ),
    )
    op.create_index("ix_provider_configs_tenant_id", "provider_configs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_provider_configs_tenant_id", table_name="provider_configs")
    op.drop_table("provider_configs")
