"""Таблица маршрутизации ``task_type → провайдер`` + структурное enforcement §6.6/§6.4.

ЧИСТЫЙ слой без I/O и без config: `resolve_route` отображает `LLMRequest` в
:class:`RouteDecision` (провайдер + регион egress + ПД-флаг + причина). Доступность
провайдера и fallback-цепочка — забота `router.LLMRouter` (нужен config); здесь только
детерминированное правило, которое юнит-тестируется без сети и без кредов.

Два инварианта закодированы СТРУКТУРНО, а не комментарием:

* **§6.6 (RU-default, AC-2).** `content_gen`/`schema_gen` — это контент с ПД клиента.
  Иностранный `provider_override` на такой задаче НЕ применяется: маршрут принудительно
  понижается на RU-дефолт (`_downgrade_to_ru`). Opt-in иностранного возможен только для
  НЕ-ПД задач (`batch`). Отказ фиксируется в ``RouteDecision.refused_override``.
* **§6.4/NFR-2 (probe-geo, AC-4).** Регион egress выводится ИЗ провайдера
  (`egress_for`): любой иностранный провайдер ⇒ egress ``"foreign"`` (зарубежная нода),
  RU/OSS ⇒ ``"ru"``. `assert_geo` рвёт любое решение, где иностранный провайдер оказался
  бы с РФ-egress — «ноль РФ-IP к ChatGPT/Perplexity» нельзя нарушить конструктивно.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from wizor.llm_router.schemas import (
    FOREIGN_PROVIDERS,
    OSS_PROVIDERS,
    RU_PROVIDERS,
    LLMRequest,
    Provider,
    TaskType,
)

Egress = Literal["ru", "foreign"]
"""Регион исходящего вызова. ``foreign`` = зарубежная нода (обязательна для инопровайдеров)."""

# Задачи с ПД клиента → RU-default, иностранный override отклоняется (§6.6).
# content_gen (FAQ/тексты клиента) и schema_gen (разметка по данным клиента) — оба ПД.
PD_TASK_TYPES: frozenset[TaskType] = frozenset({"content_gen", "schema_gen"})

# Таблица дефолтных маршрутов task_type → провайдер (без override).
# content_gen/schema_gen → GigaChat (RU-default, primary; fallback-цепочка → YandexGPT
# строится в router.py). batch → vLLM (OSS self-hosted, batch-cost). probe → OpenAI
# (иностранный канal, geo-aware; конкретный инопровайдер может быть переопределён тенантом).
_DEFAULT_ROUTES: dict[TaskType, Provider] = {
    "content_gen": "gigachat",
    "schema_gen": "gigachat",
    "batch": "vllm",
    "probe": "openai",
}

# RU-fallback-цепочка для ПД-задач: primary → secondary. НИКОГДА не содержит инопровайдера
# (иначе ПД клиента ушли бы за рубеж) — это и есть «не тихий иностранный fallback».
_RU_DEFAULT_CHAIN: tuple[Provider, ...] = RU_PROVIDERS


class ProbeGeoViolationError(RuntimeError):
    """§6.4/NFR-2 нарушено: иностранный провайдер получил бы РФ-egress (РФ-IP к ChatGPT)."""


@dataclass(frozen=True)
class RouteDecision:
    """Результат маршрутизации: куда и как уходит вызов + аудиторский след причины."""

    provider: Provider
    egress: Egress
    contains_pd: bool
    reason: str
    refused_override: Provider | None = None
    """Иностранный override, отклонённый по §6.6 (для лога/аудита), иначе ``None``."""


def egress_for(provider: Provider) -> Egress:
    """Регион egress провайдера. Инопровайдер ⇒ только зарубежная нода (§6.4/NFR-2)."""
    return "foreign" if provider in FOREIGN_PROVIDERS else "ru"


def ru_default_chain() -> tuple[Provider, ...]:
    """RU-fallback-цепочка для ПД-задач (primary→secondary), без инопровайдеров (§6.6)."""
    return _RU_DEFAULT_CHAIN


def _decide(
    provider: Provider, *, contains_pd: bool, reason: str, refused: Provider | None = None
) -> RouteDecision:
    """Собрать решение, ВСЕГДА выводя egress из провайдера (внутренняя консистентность)."""
    return RouteDecision(
        provider=provider,
        egress=egress_for(provider),
        contains_pd=contains_pd,
        reason=reason,
        refused_override=refused,
    )


def resolve_route(req: LLMRequest) -> RouteDecision:
    """Отобразить запрос в маршрут (чистая функция; доступность решает router.py).

    Порядок правил:

    1. ``probe`` — отдельный канал: всегда иностранная/geo-aware нода (egress foreign),
       ПД клиента нет (запрашиваем публичную модель о бренде). Override уважается только
       если это тоже иностранный провайдер; иначе — дефолтный инопровайдер канала.
    2. Override на ПД-задаче (`content_gen`/`schema_gen`): иностранный ⇒ ОТКАЗ + downgrade
       на RU-default (§6.6). RU/OSS override — уважается.
    3. Override на не-ПД задаче (`batch`): уважается любой (opt-in иностранного, AC-2).
    4. Нет override — дефолт по таблице.
    """
    task = req.task_type
    override = req.provider_override
    contains_pd = task in PD_TASK_TYPES

    if task == "probe":
        return _resolve_probe(override)

    if override is not None:
        if contains_pd and override in FOREIGN_PROVIDERS:
            # §6.6: ПД клиента НЕ уходят к иностранному провайдеру даже по явному override.
            return _decide(
                _DEFAULT_ROUTES[task],
                contains_pd=True,
                reason="foreign_override_refused_pd",
                refused=override,
            )
        # Не-ПД задача, либо RU/OSS override — opt-in уважается (AC-2/AC-3).
        return _decide(override, contains_pd=contains_pd, reason="tenant_override")

    return _decide(_DEFAULT_ROUTES[task], contains_pd=contains_pd, reason="default")


def _resolve_probe(override: Provider | None) -> RouteDecision:
    """Probe-канал: всегда зарубежная/geo-aware нода (§6.4/NFR-2), без ПД клиента.

    Тенант может переназначить КОНКРЕТНЫЙ иностранный провайдер (напр. perplexity вместо
    openai). Не-иностранный override (gigachat/yandexgpt/vllm) для probe допустим —
    это опрос RU-модели о бренде, egress тогда ``ru`` (РФ-IP к RU-модели легитимен, §6.4
    ограничивает лишь ChatGPT/Perplexity). Дефолт канала — иностранный провайдер.
    """
    provider = override if override is not None else _DEFAULT_ROUTES["probe"]
    return _decide(provider, contains_pd=False, reason="probe_geo")


def assert_geo(decision: RouteDecision) -> None:
    """Структурный предохранитель §6.4/NFR-2: инопровайдер ⇒ обязателен зарубежный egress.

    Ловит любое (в т.ч. сконструированное в обход `resolve_route`) решение, где иностранный
    провайдер получил бы РФ-egress — «ноль РФ-IP к ChatGPT/Perplexity». Вызывается роутером
    ПЕРЕД диспатчем; несоответствие egress провайдеру → :class:`ProbeGeoViolationError`.
    """
    if decision.egress != egress_for(decision.provider):
        msg = (
            f"probe-geo нарушен: provider={decision.provider} требует "
            f"egress={egress_for(decision.provider)!r}, получено {decision.egress!r} "
            f"(§6.4/NFR-2: инопровайдер только через зарубежную ноду)."
        )
        raise ProbeGeoViolationError(msg)


def is_foreign(provider: Provider) -> bool:
    """Иностранный ли провайдер (для явных compliance-проверок вызывающих)."""
    return provider in FOREIGN_PROVIDERS


def is_oss(provider: Provider) -> bool:
    """OSS self-hosted ли провайдер (vLLM) — batch-cost без ПД."""
    return provider in OSS_PROVIDERS
