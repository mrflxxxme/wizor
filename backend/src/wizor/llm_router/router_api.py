"""FastAPI-роутер llm-router: routing-preview + список провайдеров тенанта (P4).

Два read-only эндпоинта поверх ``provider_configs`` тенанта:

* ``GET /api/v1/llm/route?task_type=content_gen`` — какой провайдер БЫЛ БЫ выбран для
  тенанта (routing preview, AC-1/AC-2). Решение делегируется доменному
  :class:`LLMRouter` (строится параллельно llm-router-specialist'ом): грузим оверрайды
  тенанта из БД и просим роутер вернуть провайдера. Реальный вызов провайдера НЕ
  выполняется. Если доменный роутер ещё недоступен — 200 с явным телом (``resolved=false``),
  а не 500: preview деградирует мягко.
* ``GET /api/v1/llm/providers`` — routing-оверрайды тенанта (``provider_configs``).

Тенант берётся из ``request.state`` (§6.8), НЕ из тела/квери: без ``X-Tenant-Id`` → 400.
``task_type``/``provider_override`` валидируются как ``Literal`` из schemas (422 на мусор).

Ожидаемый шов доменного роутера (feature-detected, не жёсткая зависимость)::

    async def preview_route(
        *, task_type: TaskType,
        tenant_configs: list[ProviderConfigDTO],
        provider_override: Provider | None,
    ) -> Provider
"""

from __future__ import annotations

import importlib
import uuid
from typing import Annotated, Protocol, runtime_checkable

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.core.tenancy import get_tenant_id
from wizor.db.session import get_session
from wizor.llm_router import repository
from wizor.llm_router.schemas import Provider, ProviderConfigDTO, TaskType

router = APIRouter(prefix="/api/v1/llm", tags=["llm-router"])
logger = structlog.get_logger(__name__)


@runtime_checkable
class _RoutingPreview(Protocol):
    """Минимальный шов доменного роутера, нужный preview-эндпоинту (structural typing)."""

    async def preview_route(
        self,
        *,
        task_type: TaskType,
        tenant_configs: list[ProviderConfigDTO],
        provider_override: Provider | None,
    ) -> Provider:
        """Вернуть провайдера, который БЫЛ БЫ выбран (чистое решение, без вызова)."""
        ...  # pragma: no cover — Protocol-заглушка


class RouteResponse(BaseModel):
    """Ответ ``GET /route``: превью маршрутизации (AC-1/AC-2)."""

    task_type: TaskType
    provider: Provider | None
    override_applied: bool
    resolved: bool
    detail: str


def _load_router() -> _RoutingPreview | None:
    """Лениво подтянуть доменный :class:`LLMRouter` (строится параллельно).

    Динамический импорт (не статический), чтобы preview не ломался, пока доменный модуль
    ещё не готов. Нет модуля/класса/метода ``preview_route`` или конструктор упал → ``None``
    (эндпоинт вернёт мягкий 200). Точка для monkeypatch в unit-тестах.
    """
    try:
        module = importlib.import_module("wizor.llm_router.router")
    except ImportError:
        return None
    router_cls = getattr(module, "LLMRouter", None)
    if router_cls is None:
        return None
    try:
        instance = router_cls()
    except Exception:
        # Параллельная сборка: любой сбой конструктора доменного роутера → мягкий preview
        # (логируем причину, не роняем эндпоинт). Не тихий pass: причина уходит в лог.
        logger.debug("llm.router.preview_unavailable", reason="constructor_failed")
        return None
    if not isinstance(instance, _RoutingPreview):
        return None
    return instance


def _require_tenant(request: Request) -> uuid.UUID:
    """Достать тенанта из контекста запроса или отклонить (400, §6.8)."""
    tenant_id = get_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant is required (X-Tenant-Id)",
        )
    return tenant_id


@router.get(
    "/route",
    response_model=RouteResponse,
    summary="Превью маршрутизации: какой провайдер был бы выбран (AC-1/AC-2)",
)
async def preview_route(
    request: Request,
    task_type: TaskType,
    session: Annotated[AsyncSession, Depends(get_session)],
    provider_override: Provider | None = None,
) -> RouteResponse:
    """Показать провайдера, который БЫЛ БЫ выбран для тенанта под ``task_type``.

    Тенант обязателен (без ``X-Tenant-Id`` → 400, §6.8). Грузим оверрайды тенанта из
    ``provider_configs`` и делегируем решение доменному :class:`LLMRouter` (AC-1: content_gen
    без override → RU-провайдер; AC-2: opt-in иностранный только по явному override и только
    там, где §6.6 не нарушается — роутер сам решает). Реальный вызов провайдера не идёт.
    Доменный роутер недоступен → 200 с ``resolved=false`` (мягкая деградация preview).
    """
    tenant_id = _require_tenant(request)
    tenant_configs = await repository.load_provider_configs(
        session, tenant_id=tenant_id, task_type=task_type
    )

    domain_router = _load_router()
    if domain_router is None:
        return RouteResponse(
            task_type=task_type,
            provider=None,
            override_applied=False,
            resolved=False,
            detail="domain LLMRouter unavailable; routing preview pending",
        )

    provider = await domain_router.preview_route(
        task_type=task_type,
        tenant_configs=tenant_configs,
        provider_override=provider_override,
    )
    override_applied = provider_override is not None and provider == provider_override

    # Стаб `llm.call.completed` — место, где реальный вызов провайдера логировался бы для
    # cost-tracking (контракт llm-router). В preview вызова нет → stub=True.
    logger.info(
        "llm.call.completed",
        stub=True,
        preview=True,
        tenant_id=str(tenant_id),
        task_type=task_type,
        provider=provider,
        override_applied=override_applied,
    )

    return RouteResponse(
        task_type=task_type,
        provider=provider,
        override_applied=override_applied,
        resolved=True,
        detail="routed by domain LLMRouter",
    )


@router.get(
    "/providers",
    response_model=list[ProviderConfigDTO],
    summary="Routing-оверрайды провайдеров тенанта (provider_configs)",
)
async def list_providers(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProviderConfigDTO]:
    """Вернуть routing-оверрайды текущего тенанта (tenant-scoped, §6.8).

    Тенант обязателен (без ``X-Tenant-Id`` → 400). Пусто → ``[]`` (у тенанта нет
    явных оверрайдов; роутер применит дефолты).
    """
    tenant_id = _require_tenant(request)
    return await repository.load_provider_configs(session, tenant_id=tenant_id)
