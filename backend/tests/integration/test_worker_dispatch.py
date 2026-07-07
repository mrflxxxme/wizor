"""Integration: живой диспатч ``wizor.crawl_site`` через реальный Celery-воркер.

Регрессия дефекта P2/P5: модуль задач вне ``include`` воркер не импортирует —
брокер принимает сообщение, воркер отбрасывает его как unregistered, а API уже
ответил ``accepted``. ``celery inspect ping`` (live-gold шаг CI) этого не ловит,
поэтому здесь настоящая задача проходит end-to-end: send_task → воркер (поток,
solo-pool) → persist в Postgres → результат через backend.

Сайт тестового тенанта — ``https://example.test`` (RFC 2606, DNS не резолвится):
краул завершается wholesale-сбоем, но задача обязана штатно сохранить
``CrawlResult`` с ``error`` и вернуть результат (AC-6 fault-isolation).
Диспатчим ДВЕ задачи подряд: воркер живёт дольше одной задачи, каждый
``asyncio.run`` создаёт новый event loop — кеш движка БД не должен протекать
между задачами (см. докстринг ``conftest.fresh_engine``).
"""

from __future__ import annotations

import asyncio

import pytest
from celery.contrib.testing.worker import start_worker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from wizor.core.config import get_settings
from wizor.iam.seed import TEST_SITE_ID, TEST_TENANT_ID
from wizor.worker.celery_app import celery_app

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_crawl_site_dispatched_through_live_worker() -> None:
    crawl_ids: list[str] = []
    with start_worker(celery_app, perform_ping_check=False, loglevel="info"):
        for _ in range(2):
            async_result = celery_app.send_task(
                "wizor.crawl_site", args=[str(TEST_SITE_ID), str(TEST_TENANT_ID)]
            )
            payload = await asyncio.to_thread(async_result.get, 120)
            assert payload["site_id"] == str(TEST_SITE_ID)
            # example.test не резолвится — wholesale-сбой, но результат сохранён.
            assert payload["pages"] == 0
            crawl_ids.append(str(payload["crawl_result_id"]))

    # Persist проверяем отдельным движком: loop задач жил в потоке воркера,
    # модульный кеш движка использовать отсюда нельзя.
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            for crawl_id in crawl_ids:
                row = (
                    await conn.execute(
                        text(
                            "SELECT tenant_id, pages_json, read_only_confirmed "
                            "FROM crawl_results WHERE id = :id"
                        ),
                        {"id": crawl_id},
                    )
                ).one()
                assert str(row.tenant_id) == str(TEST_TENANT_ID)
                assert row.pages_json == []
    finally:
        async with engine.begin() as conn:
            for crawl_id in crawl_ids:
                await conn.execute(
                    text("DELETE FROM crawl_results WHERE id = :id"), {"id": crawl_id}
                )
        await engine.dispose()
