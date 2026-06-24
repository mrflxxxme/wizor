"""Unit: Celery ping-таска выполняется локально (без брокера) — AC-7/FR-P1-4."""

from __future__ import annotations

from wizor.worker.tasks import ping


def test_ping_returns_pong() -> None:
    # .apply() выполняет задачу синхронно в процессе, брокер не нужен.
    result = ping.apply()
    assert result.get() == "pong"
