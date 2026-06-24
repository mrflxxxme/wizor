"""Multi-tenancy: извлечение ``tenant_id`` из запроса (инвариант §6.8).

P1 — skeleton: ``tenant_id`` берётся из заголовка ``X-Tenant-Id``. В P9 источником
станет JWT (Keycloak), но контракт ``request.state.tenant_id`` стабилен — downstream
код уже сейчас читает тенант единообразно и не зависит от способа аутентификации.

Изоляция данных (нет cross-tenant утечки) обеспечивается на уровне приложения:
каждый запрос к данным обязан фильтроваться по ``tenant_id`` из контекста.
RLS-политики Postgres — план P9 (см. iam/models.py).
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

TENANT_HEADER = "X-Tenant-Id"

logger = structlog.get_logger(__name__)


def _parse_tenant_id(raw: str | None) -> uuid.UUID | None:
    """Распарсить заголовок тенанта в UUID; невалидное значение → ``None``."""
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


class TenancyMiddleware(BaseHTTPMiddleware):
    """Кладёт ``request.state.tenant_id`` (``uuid.UUID | None``) на каждый запрос."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        tenant_id = _parse_tenant_id(request.headers.get(TENANT_HEADER))
        request.state.tenant_id = tenant_id
        # tenant_id попадает в contextvars лога → виден во всех записях запроса.
        structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id) if tenant_id else None)
        try:
            return await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("tenant_id")


def get_tenant_id(request: Request) -> uuid.UUID | None:
    """Хелпер для роутов/зависимостей: текущий тенант из контекста запроса."""
    return getattr(request.state, "tenant_id", None)
