"""Точка входа FastAPI: health, метрики, CORS, tenancy, structlog.

P1 не содержит продуктовых эндпоинтов (краулер/probe/score — P2+). Это базовый
каркас, на который ложатся последующие фазы: единый lifespan, аналитика на
``app.state``, multi-tenant middleware и observability (Prometheus + JSON-логи).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from starlette.responses import JSONResponse

from wizor import __version__
from wizor.analytics.posthog import build_analytics_client
from wizor.core.config import Settings, get_settings
from wizor.core.logging import configure_logging, get_logger
from wizor.core.tenancy import TenancyMiddleware, get_tenant_id

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Старт/стоп приложения: логирование, клиент аналитики на app.state."""
    settings: Settings = get_settings()
    configure_logging(settings.log_level)
    app.state.settings = settings
    app.state.analytics = build_analytics_client(
        api_key=settings.posthog_api_key, host=settings.posthog_host
    )
    logger.info(
        "app_startup",
        app=settings.app_name,
        env=settings.environment,
        data_region=settings.data_region,
        version=__version__,
    )
    try:
        yield
    finally:
        app.state.analytics.shutdown()
        logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Собрать и сконфигурировать приложение (factory pattern для тестов/uvicorn)."""
    settings = get_settings()
    app = FastAPI(
        title="WIZOR API",
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TenancyMiddleware)

    # /metrics — Prometheus exposition (NFR observability).
    app.mount("/metrics", make_asgi_app())

    @app.get("/health")
    async def health(request: Request) -> JSONResponse:
        """Liveness/tenancy-probe. tenant = значение X-Tenant-Id или null (AC-4)."""
        tenant_id = get_tenant_id(request)
        payload: dict[str, Any] = {
            "status": "ok",
            "tenant": str(tenant_id) if tenant_id else None,
            "version": __version__,
            "data_region": request.app.state.settings.data_region,
        }
        return JSONResponse(payload)

    return app


app = create_app()
