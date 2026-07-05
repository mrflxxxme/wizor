"""FastAPI-роутер crawler: enqueue read-only краула сайта (P2, T7).

``POST /api/v1/sites/{site_id}/crawl`` ставит Celery-задачу ``crawl_site`` в очередь
и немедленно отвечает ``202 Accepted`` с идентификатором задачи (async-паттерн:
клиент опрашивает статус позже). Тенант берётся из ``request.state`` (core.tenancy),
НЕ из тела — источник истины по тенанту един для всего API (§6.8). Тело запроса нет:
цель краула однозначно задаётся ``site_id`` (сам сайт tenant-scoped в БД).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from wizor.core.tenancy import get_tenant_id
from wizor.crawler.tasks import crawl_site

router = APIRouter(prefix="/api/v1", tags=["crawler"])


class CrawlEnqueueResponse(BaseModel):
    """Ответ на постановку краула в очередь (202)."""

    task_id: str
    site_id: uuid.UUID
    status: str = "accepted"


@router.post(
    "/sites/{site_id}/crawl",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=CrawlEnqueueResponse,
    summary="Поставить read-only краул сайта в очередь",
)
async def enqueue_crawl(site_id: uuid.UUID, request: Request) -> CrawlEnqueueResponse:
    """Поставить ``crawl_site`` в очередь для ``site_id`` текущего тенанта.

    Тенант обязателен: без ``X-Tenant-Id`` (→ ``request.state.tenant_id is None``)
    краулить нечего в рамках изоляции — ``400``. Возвращает ``task_id`` для опроса.
    """
    tenant_id = get_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant is required (X-Tenant-Id)",
        )

    async_result = crawl_site.delay(str(site_id), str(tenant_id))
    return CrawlEnqueueResponse(task_id=async_result.id, site_id=site_id)
