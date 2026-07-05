"""FastAPI-роутер scoring: расчёт AI-Readiness Score сайта (P3, T5).

``GET /api/v1/sites/{site_id}/score`` — синхронный расчёт поверх последнего краула
(P2): загрузить `crawl_results` тенанта+сайта → прогнать детерминированный
:class:`ScoringEngine` (+ :class:`ProjectionEngine` по стаб-фиксам) → сохранить
`score_results` → вернуть ``{score, components[], projection[]}``. Тенант берётся из
``request.state`` (§6.8), НЕ из тела: без ``X-Tenant-Id`` → 400. Нет краула → 404.
Невалидный `site_id` → 422 (path-валидация FastAPI). Эмитит `score.calculated` (стаб).
"""

from __future__ import annotations

import datetime
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from wizor.core.tenancy import get_tenant_id
from wizor.db.session import get_session
from wizor.scoring import repository
from wizor.scoring.engine import ScoringEngine
from wizor.scoring.projection import ProjectionEngine, derive_stub_fixes
from wizor.scoring.schemas import ScoreComponent, ScoreProjection

router = APIRouter(prefix="/api/v1", tags=["scoring"])
logger = structlog.get_logger(__name__)

_engine = ScoringEngine()
_projection_engine = ProjectionEngine(_engine)


class ScoreResponse(BaseModel):
    """Ответ ``GET /score``: Score + раскрытые компоненты + Readiness-проекция (AC-3/AC-4)."""

    score: float
    score_version: str
    components: list[ScoreComponent]
    projection: list[ScoreProjection]
    calculated_at: datetime.datetime


@router.get(
    "/sites/{site_id}/score",
    response_model=ScoreResponse,
    summary="Рассчитать AI-Readiness Score сайта (детерминированный)",
)
async def get_site_score(
    site_id: uuid.UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScoreResponse:
    """Рассчитать Score сайта `site_id` текущего тенанта поверх последнего краула.

    Тенант обязателен (без ``X-Tenant-Id`` → 400, §6.8). Нет `crawl_results` для сайта →
    404 (скорить нечего). Расчёт детерминирован (AC-1); момент времени инъектируется на
    границе. Результат персистится (tenant-scoped) и возвращается пользователю.
    """
    tenant_id = get_tenant_id(request)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant is required (X-Tenant-Id)",
        )

    crawl = await repository.load_latest_crawl(session, tenant_id=tenant_id, site_id=site_id)
    if crawl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no crawl_results for site; run a crawl first",
        )

    audit_summary = crawl.audit_summary_json
    site_url = await repository.load_site_url(session, tenant_id=tenant_id, site_id=site_id) or ""
    # Момент времени инъектируется на границе — движок остаётся чистым (AC-1).
    calculated_at = datetime.datetime.now(tz=datetime.UTC)

    result = _engine.score_audit(audit_summary, calculated_at=calculated_at, site_url=site_url)
    projection = _projection_engine.project(
        audit_summary,
        derive_stub_fixes(audit_summary),
        calculated_at=calculated_at,
        site_url=site_url,
    )
    result = result.model_copy(update={"projection": projection})

    await repository.save_score_result(session, tenant_id=tenant_id, site_id=site_id, result=result)
    await session.commit()

    # Событие score.calculated (P3-стаб: структурный лог; реальная шина — позже).
    logger.info(
        "score.calculated",
        tenant_id=str(tenant_id),
        site_id=str(site_id),
        score=result.score,
        score_version=result.score_version,
        components=len(result.components),
        projections=len(projection),
    )

    return ScoreResponse(
        score=result.score,
        score_version=result.score_version,
        components=result.components,
        projection=projection,
        calculated_at=result.calculated_at,
    )
