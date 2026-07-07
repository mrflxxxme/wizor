"""Конфигурация probe-раннера через Pydantic Settings (P5).

Держит параметры dual-geo диспатча: зарубежные прокси для иностранных моделей (§6.4),
таймаут HTTP, дефолтное число прогонов (N≥5, FR-2.3) и дефолтный набор бренд/домен-термов
для эвристики mention/citation.

Секреты (proxy credentials) приходят ТОЛЬКО из окружения / Yandex Lockbox (§9, инвариант 9),
никогда не хардкодятся: дефолт пустой. Пустой пул зарубежных прокси ⇒ иностранные модели
«недоступны» (как no-op-провайдеры P4/stub-адаптеры P2) — probe к ChatGPT/Perplexity НЕ
уходит с РФ-IP молча, а честно отдаётся error-прогоном (см. ``runner``/``geo``).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# Минимум прогонов на промпт×модель (charter §6.7, FR-2.3, AC-3). Зеркалит llm_router.MIN_RUNS.
DEFAULT_N_RUNS = 5


def _split_csv(raw: str) -> tuple[str, ...]:
    """Разобрать comma-separated строку в кортеж непустых значений без дублей (порядок сохранён)."""
    seen: list[str] = []
    for item in raw.split(","):
        value = item.strip()
        if value and value not in seen:
            seen.append(value)
    return tuple(seen)


class ProbeSettings(BaseSettings):
    """Типизированные настройки probe-раннера. Источник — окружение / ``.env`` / Lockbox."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WIZOR_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Зарубежные прокси для иностранных моделей (§6.4/NFR-2) ---
    # Первичный резидентный прокси зарубежной ноды (Hetzner/Selectel + Smartproxy/BrightData).
    # Пусто ⇒ иностранные probe невозможны (иначе они ушли бы с РФ-IP — запрещено).
    probe_proxy_foreign: str = ""
    # Дополнительный пул прокси для ротации (comma-separated URL). Объединяется с primary.
    probe_proxy_pool: str = ""

    # --- HTTP / прогоны ---
    probe_http_timeout_s: float = 30.0
    probe_n_runs: int = DEFAULT_N_RUNS

    # --- Источник бренд/домен-термов для эвристики mention/citation (comma-separated) ---
    # Дефолт пуст: термы конкретного сайта передаёт вызывающий (crawler/geo-domain-expert).
    probe_brand_terms: str = ""

    def proxy_pool(self) -> tuple[str, ...]:
        """Полный пул зарубежных прокси: primary + pool, без пустых и дублей (для ротации)."""
        return _split_csv(f"{self.probe_proxy_foreign},{self.probe_proxy_pool}")

    def foreign_proxy_configured(self) -> bool:
        """§6.4: сконфигурирован ли хотя бы один зарубежный прокси.

        Пусто ⇒ иностранные модели недоступны — probe к ChatGPT/Perplexity НЕ уходит с РФ-IP
        (отдаётся error-прогоном раннера, не тихий RU-fallback).
        """
        return bool(self.proxy_pool())

    def brand_terms(self) -> tuple[str, ...]:
        """Дефолтные бренд/домен-термы (обычно переопределяются per-site вызывающим)."""
        return _split_csv(self.probe_brand_terms)


@lru_cache(maxsize=1)
def get_probe_settings() -> ProbeSettings:
    """Кешированный синглтон настроек probe (один разбор окружения на процесс)."""
    return ProbeSettings()
