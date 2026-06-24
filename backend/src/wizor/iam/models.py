"""IAM-модели: ``tenants``, ``users``, ``sites`` (multi-tenant skeleton, §6.8).

``Tenant`` — корень изоляции (сам не несёт ``tenant_id``, он и есть тенант).
``User`` и ``Site`` несут ``tenant_id`` через :class:`TenantMixin` (одна колонка,
индексирована) и привязаны к тенанту через ``ForeignKeyConstraint`` в
``__table_args__`` — без повторного маппинга колонки. Уникальность email — в
пределах тенанта. Полные поля IAM (sessions, consents, DPA-акцепты, entitlements)
добавляются в P9 (см. contracts/iam).
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wizor.db.base import Base, TenantMixin, TimestampMixin


class Tenant(Base, TimestampMixin):
    """Арендатор (организация-клиент) — корень multi-tenant изоляции."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    users: Mapped[list[User]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    sites: Mapped[list[Site]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base, TenantMixin, TimestampMixin):
    """Пользователь, привязанный к тенанту. Email уникален в пределах тенанта."""

    __tablename__ = "users"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_users_tenant"
        ),
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    # Линковка с Keycloak — заполняется в P9 (полная auth).
    keycloak_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class Site(Base, TenantMixin, TimestampMixin):
    """Сайт клиента (объект аудита). Привязан к тенанту."""

    __tablename__ = "sites"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE", name="fk_sites_tenant"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    tenant: Mapped[Tenant] = relationship(back_populates="sites")
