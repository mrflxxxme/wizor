"""Конфигурация приложения через Pydantic Settings (no magic strings).

Инвариант §6.6 (152-ФЗ резидентность): ПД клиентов хостятся/обрабатываются в РФ.
Поэтому ``data_region`` валидируется как РФ-регион (Yandex Cloud ru-central1) —
любое не-РФ значение валит старт приложения. Секреты приходят только из окружения
(``.env`` не коммитится; реальные значения — в Yandex Lockbox), §6.9.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Разрешённые регионы хранения/обработки ПД (NFR-1). Только РФ.
_ALLOWED_DATA_REGIONS = ("ru-central1",)


class Settings(BaseSettings):
    """Типизированные настройки. Источник — переменные окружения / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WIZOR_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "wizor-api"
    environment: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    log_level: str = "INFO"

    # --- 152-ФЗ резидентность (NFR-1) ---
    data_region: str = "ru-central1"

    # --- HTTP / CORS ---
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Datastores (дефолты — для dev-compose; в prod приходят из Lockbox) ---
    database_url: str = "postgresql+asyncpg://wizor:wizor@localhost:5432/wizor"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # --- PostHog (NFR-7) ---
    # В P1 self-hosted инстанс не поднимается (deferred_live_gold). Если ключ пуст —
    # capture превращается в no-op (см. analytics.posthog). Это осознанное P1-поведение.
    posthog_api_key: str = ""
    posthog_host: str = "http://localhost:8000"

    # --- Keycloak (skeleton; полная auth → P9) ---
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "wizor-dev"
    keycloak_client_id: str = "wizor-api"

    @field_validator("data_region")
    @classmethod
    def _enforce_ru_residency(cls, value: str) -> str:
        """ПД только в РФ — иначе старт запрещён (NFR-1, инвариант §6.6)."""
        if value not in _ALLOWED_DATA_REGIONS:
            allowed = ", ".join(_ALLOWED_DATA_REGIONS)
            raise ValueError(
                f"data_region={value!r} нарушает 152-ФЗ резидентность; "
                f"разрешены только РФ-регионы: {allowed}"
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Кешированный синглтон настроек (один разбор окружения на процесс)."""
    return Settings()
