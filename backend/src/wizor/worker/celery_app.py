"""Celery-приложение (брокер/бэкенд — Redis), конфиг из настроек.

P1 — базовый каркас очередей: один воркер, очередь ``default``, smoke ``ping``.
Реальные задачи (краул, probe, скоринг) появляются в P2+.
"""

from __future__ import annotations

from celery import Celery

from wizor.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "wizor",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=["wizor.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="default",
    broker_connection_retry_on_startup=True,
)
