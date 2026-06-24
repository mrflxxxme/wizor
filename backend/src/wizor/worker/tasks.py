"""Celery-задачи P1. Только ``ping`` для smoke-проверки очереди (AC-7 / FR-P1-4)."""

from __future__ import annotations

from wizor.worker.celery_app import celery_app


@celery_app.task(name="wizor.ping")  # type: ignore[untyped-decorator]  # Celery decorator не типизирован
def ping() -> str:
    """Минимальная задача: подтверждает, что брокер/воркер живы. Возвращает 'pong'."""
    return "pong"
