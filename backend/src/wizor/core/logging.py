"""Структурное JSON-логирование через structlog (Loki-ready, OpenTelemetry-friendly).

JSON-рендер выбран осознанно: dev-compose отдаёт логи в stdout, prod — в Loki;
один формат на оба окружения упрощает observability (PRD §12 / conventions).
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Сконфигурировать stdlib + structlog на единый JSON-вывод в stdout."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Вернуть связанный structlog-логгер."""
    # structlog.get_logger типизирован как Any; фиксируем контракт через cast.
    return cast("structlog.stdlib.BoundLogger", structlog.get_logger(name))
