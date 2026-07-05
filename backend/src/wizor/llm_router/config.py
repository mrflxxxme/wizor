"""Конфигурация провайдеров LLM-роутера через Pydantic Settings (P4).

Все креды провайдеров — PLACEHOLDER'ы: дефолт пустой/``None``, реальные значения
приходят ТОЛЬКО из окружения / Yandex Lockbox (§6.9 — ключ никогда не в коде). Пустой
ключ ⇒ провайдер «недоступен» (``is_configured`` → ``False``), как no-op PostHog в P1
или stub-адаптеры в P2 — вызов такого провайдера не уходит в сеть, а изолируется
роутером (fallback по RU-цепочке или явная ошибка, НЕ тихий иностранный fallback).

Публичные ``*_base_url`` — это адреса API провайдеров, не секреты; их дефолты заданы для
удобства, но переопределяемы. Бюджет per-task (soft/hard) зеркалит cost-budget.yaml §3.4
(числа тюнятся там); держим их здесь как настройки, чтобы cost-guard брал один источник.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from wizor.llm_router.schemas import FOREIGN_PROVIDERS, Provider

# Регион egress для probe-канала к ИНОСТРАННЫМ моделям. §6.4/NFR-2: probe к
# ChatGPT/Perplexity никогда не с РФ-IP — только через зарубежную ноду. "ru" здесь
# структурно запрещён (валидируется), значение по умолчанию — не-РФ.
_FORBIDDEN_PROBE_EGRESS = "ru"


class LLMRouterSettings(BaseSettings):
    """Типизированные настройки провайдеров. Источник — окружение / ``.env`` / Lockbox."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="WIZOR_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- RU-провайдеры (дефолт для content_gen/schema_gen с ПД клиента, §6.6) ---
    gigachat_api_key: str = ""
    gigachat_base_url: str = "https://gigachat.devices.sberbank.ru/api/v1"
    gigachat_model: str = "GigaChat"

    yandexgpt_api_key: str = ""
    yandexgpt_folder_id: str = ""
    yandexgpt_base_url: str = "https://llm.api.cloud.yandex.net/foundationModels/v1"
    yandexgpt_model: str = "yandexgpt-lite"

    # --- OSS self-hosted (vLLM/Qwen/Saiga) для batch-cost, без ПД клиента ---
    # Пустой base_url ⇒ vLLM не поднят (deferred для devops-infra), провайдер недоступен.
    vllm_base_url: str = ""
    vllm_api_key: str = ""
    vllm_model: str = "Qwen/Qwen2.5-7B-Instruct"

    # --- Иностранные (opt-in для не-ПД задач; probe-канал через зарубежные ноды) ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    perplexity_api_key: str = ""
    perplexity_base_url: str = "https://api.perplexity.ai"
    perplexity_model: str = "sonar"

    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com/v1"
    anthropic_model: str = "claude-3-5-haiku-latest"

    gemini_api_key: str = ""
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-1.5-flash"

    # --- HTTP ---
    llm_http_timeout_s: float = 30.0

    # --- Cost-guard (зеркало cost-budget.yaml per_task §3.4; тюнится там) ---
    llm_per_task_soft_usd: float = 0.40
    llm_per_task_hard_usd: float = 1.50

    # --- Probe geo (§6.4/NFR-2) ---
    # Регион зарубежной ноды probe-egress. Значение "ru" структурно запрещено ниже.
    probe_egress_region: str = "eu-foreign"

    def api_key(self, provider: Provider) -> str:
        """Вернуть API-ключ провайдера (пустая строка = не сконфигурирован)."""
        return str(getattr(self, f"{provider}_api_key", ""))

    def base_url(self, provider: Provider) -> str:
        """Вернуть base_url провайдера."""
        return str(getattr(self, f"{provider}_base_url", ""))

    def model_name(self, provider: Provider) -> str:
        """Вернуть имя модели провайдера по умолчанию."""
        return str(getattr(self, f"{provider}_model", ""))

    def is_configured(self, provider: Provider) -> bool:
        """Сконфигурирован ли провайдер (есть ли креды/endpoint для реального вызова).

        vLLM (OSS self-hosted) не требует ключа — достаточно ``base_url`` (endpoint ноды).
        Остальные требуют непустой API-ключ. Пустой ⇒ провайдер недоступен: роутер не
        уйдёт к нему в сеть, а изолирует (RU-fallback / явная ошибка), §6.9.
        """
        if provider == "vllm":
            return bool(self.vllm_base_url.strip())
        return bool(self.api_key(provider).strip())

    def probe_egress_is_foreign(self) -> bool:
        """§6.4/NFR-2: регион probe-egress к иностранным моделям обязан быть НЕ РФ."""
        return self.probe_egress_region.strip().lower() != _FORBIDDEN_PROBE_EGRESS

    def assert_probe_egress_foreign(self) -> None:
        """Свалить конфиг, если probe-egress настроен на РФ (запрет РФ-IP к ChatGPT)."""
        if not self.probe_egress_is_foreign():
            msg = (
                f"probe_egress_region={self.probe_egress_region!r} нарушает §6.4/NFR-2: "
                f"probe к иностранным моделям ({', '.join(FOREIGN_PROVIDERS)}) "
                f"запрещён с РФ-IP — нужна зарубежная нода."
            )
            raise ValueError(msg)


@lru_cache(maxsize=1)
def get_llm_settings() -> LLMRouterSettings:
    """Кешированный синглтон настроек роутера (один разбор окружения на процесс)."""
    return LLMRouterSettings()
