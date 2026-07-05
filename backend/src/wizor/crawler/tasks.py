"""Celery-задача ``crawl_site`` — оркестрация read-only краула (P2, T6).

Поток: загрузить URL сайта (tenant-scoped) → делегировать домену ``audit_site``
(единственная точка входа crawler-модуля) → сохранить ``CrawlResult`` в БД →
эмитировать событие ``crawl.completed`` (P2: structlog-стаб, реальная шина — позже).

Fault-isolation (AC-6): пофакторный/постраничный сбой изолируется ВНУТРИ
``audit_site`` (4xx одной страницы не роняет батч) — задача сохраняет результат
как есть, включая ``result.error`` при wholesale-сбое. Транзиентные wholesale-сбои
(сеть) ретраятся через tenacity. ``audit_site`` импортируется лениво — модуль домена
собирается параллельно и не нужен на импорте задачи (celery autodiscovery).
"""

from __future__ import annotations

import asyncio
import uuid

import structlog
from sqlalchemy import select
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from wizor.crawler.repository import save_crawl_result
from wizor.crawler.schemas import CrawlResult
from wizor.db.session import get_sessionmaker
from wizor.iam.models import Site
from wizor.worker.celery_app import celery_app

logger = structlog.get_logger(__name__)

MAX_PAGES = 100
TIMEOUT_S = 300


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(OSError),
    reraise=True,
)
async def _audit_with_retry(site_url: str) -> CrawlResult:
    """Вызвать доменный ``audit_site`` с ретраями на транзиентные сетевые сбои.

    ``audit_site`` не бросает на per-page 4xx/5xx (AC-6); ретраится лишь ``OSError``
    (обрыв соединения и т.п.). Ленивый импорт — домен собирается параллельно (T1).
    """
    from wizor.crawler.audit import audit_site  # ленивый импорт домена (T1 parallel)

    # Явная аннотация: audit.py собирается параллельно (T1); до его появления mypy
    # видит вход как Any — фиксируем контракт возврата из шва schemas.CrawlResult.
    result: CrawlResult = await audit_site(site_url, max_pages=MAX_PAGES, timeout_s=TIMEOUT_S)
    return result


async def _load_site_url(tenant_id: uuid.UUID, site_id: uuid.UUID) -> str:
    """Загрузить URL сайта строго в рамках тенанта (§6.8). Нет → ``LookupError``."""
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        stmt = select(Site.url).where(Site.id == site_id, Site.tenant_id == tenant_id)
        url = (await session.execute(stmt)).scalar_one_or_none()
    if url is None:
        msg = f"site {site_id} not found for tenant {tenant_id}"
        raise LookupError(msg)
    return url


async def _run(tenant_id: uuid.UUID, site_id: uuid.UUID) -> dict[str, object]:
    """Асинхронное тело задачи: загрузка URL → аудит → persist → событие."""
    site_url = await _load_site_url(tenant_id, site_id)
    result = await _audit_with_retry(site_url)

    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        row = await save_crawl_result(session, tenant_id=tenant_id, site_id=site_id, result=result)
        await session.commit()
        crawl_result_id = row.id

    # Событие crawl.completed (P2-стаб: структурный лог; реальная шина — позже).
    logger.info(
        "crawl.completed",
        tenant_id=str(tenant_id),
        site_id=str(site_id),
        crawl_result_id=str(crawl_result_id),
        pages=len(result.pages),
        read_only_confirmed=result.read_only_confirmed,
        error=result.error,
    )
    return {
        "crawl_result_id": str(crawl_result_id),
        "site_id": str(site_id),
        "pages": len(result.pages),
        "read_only_confirmed": result.read_only_confirmed,
    }


@celery_app.task(name="wizor.crawl_site")  # type: ignore[untyped-decorator]  # Celery decorator не типизирован
def crawl_site(site_id: str, tenant_id: str) -> dict[str, object]:
    """Enqueue-точка: краул сайта ``site_id`` тенанта ``tenant_id`` (read-only).

    Аргументы — строки (JSON-сериализация брокера); парсятся в UUID. Синхронная
    Celery-обёртка гоняет async-тело в собственном loop (``asyncio.run``).
    """
    return asyncio.run(_run(uuid.UUID(tenant_id), uuid.UUID(site_id)))
