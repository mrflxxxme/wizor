"""Cost-guard: мягкий/жёсткий бюджет per-task для LLM-вызовов (AC-6).

Источник чисел — cost-budget.yaml §3.4 (per_task: soft $0.40 / hard $1.50), приходят из
`config.LLMRouterSettings` (env-переопределяемы). Guard аккумулирует стоимость по мере
вызовов (для probe — по N прогонам); превышение soft → предупреждение и продолжение,
превышение hard → отмена задачи (`CostBudgetExceededError`) + warning в лог. Оценка
стоимости до вызова — грубая эвристика по длине промпта × прайс провайдера за 1K токенов
(реальная стоимость берётся из ``LLMResponse.cost_usd`` после вызова, если провайдер её
вернул). Guard — на задачу (не глобальный синглтон): свежий per `complete`/`probe`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from wizor.llm_router.schemas import Provider

logger = structlog.get_logger(__name__)

# Грубая оценка: ~4 символа на токен (латиница/кириллица усреднённо).
_CHARS_PER_TOKEN = 4
# Множитель на ожидаемый объём completion относительно prompt (эвристика оценки cost).
_COMPLETION_FACTOR = 1.5

# Прайс за 1K токенов (USD), порядок величины для ОЦЕНКИ бюджета (не биллинг).
# RU/OSS дёшевы; иностранные дороже. Реальный cost приходит из LLMResponse.cost_usd.
_PRICE_PER_1K_USD: dict[Provider, float] = {
    "gigachat": 0.002,
    "yandexgpt": 0.002,
    "vllm": 0.0002,  # self-hosted — почти только инфра-стоимость
    "openai": 0.010,
    "anthropic": 0.015,
    "perplexity": 0.005,
    "gemini": 0.007,
}


class CostBudgetExceededError(RuntimeError):
    """Жёсткий per-task бюджет превышен — задача отменяется (AC-6)."""


def estimate_cost_usd(prompt: str, provider: Provider, *, n_runs: int = 1) -> float:
    """Грубая оценка стоимости вызова(ов) ДО обращения к провайдеру (для pre-authorize).

    Токены ≈ длина промпта / 4, плюс ожидаемый completion. Множится на N прогонов (probe).
    Это ОЦЕНКА для cost-guard, не биллинг — реальная стоимость логируется из ответа.
    """
    prompt_tokens = max(1, len(prompt) // _CHARS_PER_TOKEN)
    total_tokens = prompt_tokens * (1.0 + _COMPLETION_FACTOR) * max(1, n_runs)
    price = _PRICE_PER_1K_USD.get(provider, 0.010)
    return total_tokens / 1000.0 * price


@dataclass
class CostGuard:
    """Аккумулятор стоимости per-task с soft/hard-порогами (§3.4, AC-6)."""

    soft_cap_usd: float
    hard_cap_usd: float
    task_type: str = ""
    tenant_id: str | None = None
    _spent_usd: float = field(default=0.0, init=False)

    @property
    def spent_usd(self) -> float:
        """Накопленная стоимость задачи на текущий момент."""
        return self._spent_usd

    def pre_authorize(self, estimated_usd: float) -> None:
        """Проверить бюджет ДО вызова: если прогноз пробивает hard — отменить (raise).

        Прогноз = уже потрачено + оценка следующего вызова. Пробитие soft → warning и
        продолжение; пробитие hard → warning + :class:`CostBudgetExceededError` (AC-6).
        """
        projected = self._spent_usd + estimated_usd
        if projected > self.hard_cap_usd:
            logger.warning(
                "llm.cost.hard_cap_exceeded",
                task_type=self.task_type,
                tenant_id=self.tenant_id,
                spent_usd=round(self._spent_usd, 6),
                projected_usd=round(projected, 6),
                hard_cap_usd=self.hard_cap_usd,
            )
            msg = (
                f"per-task бюджет ${self.hard_cap_usd} пробит (прогноз ${projected:.4f}) — "
                f"задача {self.task_type!r} отменена (AC-6/§3.4)."
            )
            raise CostBudgetExceededError(msg)
        if projected > self.soft_cap_usd:
            logger.warning(
                "llm.cost.soft_cap_exceeded",
                task_type=self.task_type,
                tenant_id=self.tenant_id,
                projected_usd=round(projected, 6),
                soft_cap_usd=self.soft_cap_usd,
            )

    def record(self, actual_usd: float) -> None:
        """Учесть фактическую стоимость завершённого вызова; hard-пробитие → отмена задачи.

        Вызывается ПОСЛЕ ответа провайдера. Если факт вывел накопленное за hard —
        оставшаяся часть задачи (напр. следующие probe-прогоны) отменяется.
        """
        self._spent_usd += actual_usd
        if self._spent_usd > self.hard_cap_usd:
            logger.warning(
                "llm.cost.hard_cap_exceeded",
                task_type=self.task_type,
                tenant_id=self.tenant_id,
                spent_usd=round(self._spent_usd, 6),
                hard_cap_usd=self.hard_cap_usd,
            )
            msg = (
                f"per-task бюджет ${self.hard_cap_usd} пробит фактической стоимостью "
                f"(${self._spent_usd:.4f}) — задача {self.task_type!r} отменена (AC-6)."
            )
            raise CostBudgetExceededError(msg)
