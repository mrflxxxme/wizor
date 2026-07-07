"""FastAPI-роутер metrics: Visibility-агрегат + управление набором промптов (P5).

Три эндпоинта, все tenant-scoped (тенант из ``request.state``, §6.8; без ``X-Tenant-Id`` →
400):

* ``GET /api/v1/sites/{site_id}/visibility`` — последний агрегат Visibility (AC-4):
  ``{visibility_score, components{coverage,sov,citation_rate,stability}, ci_lower, ci_upper,
  n, prompt_set_version}``. Полоса шума CI — honest-forecast (§6.2/§6.7): диапазон, не
  гарантия. Нет агрегата → 404 (probe ещё не считался).
* ``GET /api/v1/sites/{site_id}/prompts`` — активный (последняя версия) набор промптов
  (FR-2.1). Нет набора → 404.
* ``PUT /api/v1/sites/{site_id}/prompts`` — правка набора → НОВАЯ версия (AC-5). Возвращает
  версионированный набор; исторические probe остаются привязаны к старой версии.

Невалидный ``site_id`` → 422 (path-валидация FastAPI). Управление наборами живёт в контексте
metrics намеренно: набор промптов — общий вход и probe (прогоны), и метрик (версия агрегата).
"""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.core.tenancy import get_tenant_id
from wizor.db.session import get_session
from wizor.metrics import repository as metrics_repository
from wizor.metrics.schemas import VisibilityMetrics
from wizor.probe import repository as probe_repository
from wizor.probe.schemas import PromptSetDTO

router = APIRouter(prefix="/api/v1", tags=["metrics"])
logger = structlog.get_logger(__name__)


class PromptSetUpdate(BaseModel):
    """Тело ``PUT /prompts``: новый список промптов (создаёт новую версию, AC-5)."""

    prompts: list[str] = Field(default_factory=list)


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
    "/sites/{site_id}/visibility",
    response_model=VisibilityMetrics,
    summary="Последний агрегат Visibility сайта (Score + 4 компонента + полоса шума, AC-4)",
)
async def get_site_visibility(
    site_id: uuid.UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> VisibilityMetrics:
    """Вернуть последний Visibility-агрегат сайта ``site_id`` текущего тенанта (AC-4).

    Тенант обязателен (без ``X-Tenant-Id`` → 400, §6.8). Нет агрегата → 404 (probe ещё не
    прогонялся). CI — полоса шума (§6.2/§6.7): диапазон, не гарантия.
    """
    tenant_id = _require_tenant(request)
    metrics = await metrics_repository.load_latest_visibility(
        session, tenant_id=tenant_id, site_id=site_id
    )
    if metrics is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no visibility metrics for site; run a probe batch first",
        )
    return metrics


@router.get(
    "/sites/{site_id}/prompts",
    response_model=PromptSetDTO,
    summary="Активный (последняя версия) набор промптов сайта (FR-2.1)",
)
async def get_site_prompts(
    site_id: uuid.UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PromptSetDTO:
    """Вернуть активный набор промптов сайта текущего тенанта. Нет набора → 404."""
    tenant_id = _require_tenant(request)
    prompt_set = await probe_repository.load_active_prompt_set(
        session, tenant_id=tenant_id, site_id=site_id
    )
    if prompt_set is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no prompt set for site; create one first",
        )
    return prompt_set


@router.put(
    "/sites/{site_id}/prompts",
    response_model=PromptSetDTO,
    status_code=status.HTTP_200_OK,
    summary="Обновить набор промптов сайта → новая версия (AC-5)",
)
async def put_site_prompts(
    site_id: uuid.UUID,
    body: PromptSetUpdate,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PromptSetDTO:
    """Создать новую версию набора промптов сайта (AC-5: правка не перезатирает старую).

    Тенант обязателен (без ``X-Tenant-Id`` → 400, §6.8). Новая версия = ``max+1``;
    исторические probe остаются привязаны к прежней версии.
    """
    tenant_id = _require_tenant(request)
    prompt_set = await probe_repository.upsert_prompt_set(
        session, tenant_id=tenant_id, site_id=site_id, prompts=body.prompts
    )
    await session.commit()
    logger.info(
        "prompt_set.updated",
        tenant_id=str(tenant_id),
        site_id=str(site_id),
        version=prompt_set.version,
        prompts=len(prompt_set.prompts),
    )
    return prompt_set
