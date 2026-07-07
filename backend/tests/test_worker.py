"""Unit: Celery ping-таска выполняется локально (без брокера) — AC-7/FR-P1-4."""

from __future__ import annotations

from wizor.worker.celery_app import celery_app
from wizor.worker.tasks import ping


def test_ping_returns_pong() -> None:
    # .apply() выполняет задачу синхронно в процессе, брокер не нужен.
    result = ping.apply()
    assert result.get() == "pong"


def test_include_registers_all_task_modules() -> None:
    """Регрессия P2/P5: модуль задач вне ``include`` воркер не импортирует.

    Тогда его задачи для воркера unregistered — сообщение молча отбрасывается,
    хотя API уже ответил ``accepted``. Проверяем сам конфиг (``conf.include``),
    а не только реестр: реестр в тестовом прогоне наполняется и прямыми
    импортами из других тестов, что маскировало бы регрессию.
    """
    include = set(celery_app.conf.include)
    assert {"wizor.worker.tasks", "wizor.crawler.tasks", "wizor.probe.tasks"} <= include

    # Smoke: модули из include импортируемы и регистрируют ожидаемые имена задач.
    celery_app.loader.import_default_modules()
    registered = set(celery_app.tasks)
    assert {"wizor.ping", "wizor.crawl_site", "wizor.run_probe_batch"} <= registered
