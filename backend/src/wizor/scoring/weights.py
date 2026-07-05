"""Весовая модель AI-Readiness Score (P3, домен `geo-domain-expert`).

Чистые данные + лёгкие хелперы (stdlib + typing; НИКАКИХ тяжёлых импортов). Определяет,
_с каким весом_ каждый аудит-фактор из P2 (`crawler.FactorVerdict.factor`) вносит вклад в
детерминированный Score [0..100], в каком слое (Discovery / Comprehension) он живёт и как
вердикт pass/warn/fail/deferred нормируется в значение [0..1]. Сам движок агрегации
(`ScoringEngine`) — зона `backend-implementer`; здесь только модель и нормировка.

Ключевые свойства (charter §6, phase-spec P3):

* **§6.5 инвариант — `llms.txt` НЕ весит** в citation-Score. Он структурно отсутствует в
  `WEIGHTS`; сторож `EXCLUDED_FROM_SCORE` + импорт-тайм проверка `_verify_weight_model`
  фиксируют инвариант так, чтобы grep ревьюера и AC-2-тест могли на него опереться.
* **Детерминизм** — модель — чистые данные; одинаковый `audit_summary` → одинаковый Score
  (FR-1.3 AC-1). Смена весов/набора факторов/метода нормировки = новый `SCORE_VERSION`,
  НЕ мутация истории (контракт scoring).
* **Honest-forecast (§6.2)** — Score это сигнал готовности, НЕ гарантированный Visibility-%.
  Веса — доказуемое доменное суждение (AEO/GEO citation-левера), а не обещание цитирования.
  Калибровка против реальных citation-данных — итерация после P5/P8 (вне scope P3).

Модель весов и обоснование по каждому фактору: см. `WEIGHTS.md` (RU).
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

# --------------------------------------------------------------------------- #
# Версия набора весов                                                          #
# --------------------------------------------------------------------------- #

SCORE_VERSION: Final = "1.0.0"
"""Версия весовой модели Score.

Бампится при изменении: (a) значений весов, (b) состава факторов `WEIGHTS`, (c) метода
нормировки (`normalize_verdict` / формула агрегации). НЕ бампится, когда ранее `deferred`
фактор (cwv/indexability по ключу; entity_graph/recency по экстрактору P6+) начинает
приходить со скорируемым вердиктом — это другой `audit_summary`, а не другая модель.
"""

# --------------------------------------------------------------------------- #
# Слои и доступность фактора                                                   #
# --------------------------------------------------------------------------- #

Layer = Literal["discovery", "comprehension"]
"""Слой citation-воронки: Discovery (сайт обнаружим/обходим) → Comprehension (понятен LLM)."""

DISCOVERY: Final[Layer] = "discovery"
COMPREHENSION: Final[Layer] = "comprehension"

Availability = Literal["scored", "deferred", "future"]
"""Готовность фактора к скорингу СЕГОДНЯ (P3):

* ``scored`` — P2 эмитит реальный вердикт pass/warn/fail (robots/sitemap/http/semantics/
  json_ld/faq).
* ``deferred`` — P2 эмитит фактор, но пока всегда `deferred` (stub-адаптер без ключа:
  cwv, indexability) → исключён из знаменателя до подключения источника.
* ``future`` — P2 НЕ эмитит `FactorVerdict` вовсе (экстрактор появится в P6+:
  entity_graph, recency); движок трактует отсутствие как `deferred` (без падения).
"""

# --------------------------------------------------------------------------- #
# Нормировка вердикта → [0..1]                                                 #
# --------------------------------------------------------------------------- #

TOTAL_WEIGHT: Final = 100.0
"""Сумма весов всех факторов. Score нормируется на сумму весов СКОРИРУЕМЫХ факторов."""

_WEIGHT_SUM_TOLERANCE: Final = 1e-9

_VERDICT_VALUE: Final[MappingProxyType[str, float]] = MappingProxyType(
    {
        "pass": 1.0,  # nosec B105 — вердикт аудита «pass», не пароль (B105 ложное срабатывание)
        "warn": 0.5,
        "fail": 0.0,
        # `deferred` формально маппится в 0.0, НО это значение НИКОГДА не попадает в
        # расчёт: `is_scored("deferred") is False` → фактор исключён и из числителя, и
        # из знаменателя (нейтрально, без штрафа). Значение — лишь заглушка полноты словаря.
        "deferred": 0.0,
    },
)

SCORED_VERDICTS: Final[frozenset[str]] = frozenset({"pass", "warn", "fail"})
"""Вердикты, которые ВХОДЯТ в знаменатель Score. `deferred` — вне (нейтрально, не штраф)."""


def normalize_verdict(verdict: str) -> float:
    """Свести вердикт аудит-фактора к нормированному значению [0..1].

    pass→1.0, warn→0.5, fail→0.0. `deferred` возвращает 0.0, НО его нельзя включать в
    Score напрямую — сначала проверь `is_scored(verdict)`: deferred-фактор исключается из
    знаменателя (нейтрально), а не штрафуется нулём. Неизвестный вердикт → `ValueError`.
    """
    try:
        return _VERDICT_VALUE[verdict]
    except KeyError:
        msg = f"неизвестный вердикт {verdict!r}; ожидается один из {sorted(_VERDICT_VALUE)}"
        raise ValueError(msg) from None


def is_scored(verdict: str) -> bool:
    """Входит ли фактор с таким вердиктом в знаменатель Score.

    `deferred` (нет ключа/экстрактора) → False: фактор нейтрально исключён, НЕ штрафует
    Score. Так недоступный сегодня сигнал не занижает готовность (AC-5: идеальный сайт с
    deferred cwv/indexability всё равно достигает 100).
    """
    return verdict in SCORED_VERDICTS


# --------------------------------------------------------------------------- #
# Весовая модель фактора                                                       #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class FactorWeight:
    """Вес одного аудит-фактора в AI-Readiness Score.

    `factor` совпадает с `crawler.schemas.FactorVerdict.factor` — движок джойнит модель с
    `audit_summary` по этому ключу. `weight` — пункты вклада (сумма всех = `TOTAL_WEIGHT`).
    """

    factor: str
    """Идентификатор фактора == `FactorVerdict.factor` (или future-фактор, ещё не эмитится)."""
    weight: float
    """Вес в пунктах Score (0..100). Сумма по всем факторам = `TOTAL_WEIGHT`."""
    layer: Layer
    """Слой воронки: Discovery (обнаружимость) или Comprehension (понятность для LLM)."""
    availability: Availability
    """Скорируется ли фактор сегодня, или приходит `deferred` (адаптер/экстрактор P6+)."""
    description: str
    """RU-пояснение (user-facing, AC-3): почему это citation-левер. Механизм, не гарантия %."""


# Discovery — сайт должен быть обнаружим и обходим AI-краулерами, иначе цитирование
# невозможно в принципе (жёсткий гейт воронки). Сумма слоя = 45.
_DISCOVERY: Final[tuple[FactorWeight, ...]] = (
    FactorWeight(
        factor="robots_txt",
        weight=12.0,
        layer=DISCOVERY,
        availability="scored",
        description=(
            "Директивы robots.txt для AI-ботов (GPTBot, OAI-SearchBot, PerplexityBot, "
            "YandexBot, Google-Extended) определяют, разрешён ли обход контента. Явный "
            "Disallow: / делает цитирование невозможным — жёсткий гейт Discovery."
        ),
    ),
    FactorWeight(
        factor="indexability",
        weight=10.0,
        layer=DISCOVERY,
        availability="deferred",
        description=(
            "Скорость индексации через IndexNow (Bing) и Яндекс.Вебмастер — критично для "
            "RU-поверхностей (Яндекс/Алиса-Нейро) и Bing-питаемых (ChatGPT Search, Copilot). "
            "Требует creds founder'а — до подключения приходит как deferred (не штрафует)."
        ),
    ),
    FactorWeight(
        factor="cwv",
        weight=8.0,
        layer=DISCOVERY,
        availability="deferred",
        description=(
            "Core Web Vitals (LCP/CLS/INP) — сигнал качества страницы; медленная загрузка "
            "снижает приоритет обхода. Требует внешнего источника (PageSpeed/Lighthouse) — "
            "до подключения ключа приходит как deferred (не штрафует)."
        ),
    ),
    FactorWeight(
        factor="http_status",
        weight=8.0,
        layer=DISCOVERY,
        availability="scored",
        description=(
            "HTTP-здоровье страниц (2xx/3xx против 4xx/5xx): серверные ошибки 5xx блокируют "
            "индексацию, битые 4xx дробят краул-бюджет и связность сайта."
        ),
    ),
    FactorWeight(
        factor="sitemap",
        weight=7.0,
        layer=DISCOVERY,
        availability="scored",
        description=(
            "XML sitemap ускоряет и делает полнее обнаружение страниц краулерами; без него "
            "часть контента может остаться незамеченной для AI-поиска."
        ),
    ),
)

# Comprehension — как только сайт обнаружен, эти сигналы определяют, ПОНИМАЕТ ли LLM
# сущности и извлекает ли ответы для цитирования (первичные citation-левера). Сумма = 55.
_COMPREHENSION: Final[tuple[FactorWeight, ...]] = (
    FactorWeight(
        factor="json_ld",
        weight=16.0,
        layer=COMPREHENSION,
        availability="scored",
        description=(
            "Разметка schema.org (Organization, Article, Product, HowTo, FAQPage) даёт "
            "AI-системам машиночитаемые сущности и связи — первичный Comprehension-левер, "
            "заметно повышающий шанс попасть в AI-ответ."
        ),
    ),
    FactorWeight(
        factor="faq",
        weight=16.0,
        layer=COMPREHENSION,
        availability="scored",
        description=(
            "FAQPage-разметка и answer-first блоки (короткий прямой ответ 50–150 слов) — "
            "формат, который LLM извлекают и цитируют напрямую. Ключевой AEO citation-левер."
        ),
    ),
    FactorWeight(
        factor="html_semantics",
        weight=10.0,
        layer=COMPREHENSION,
        availability="scored",
        description=(
            "Семантическая структура (единственный <h1>, иерархия h2→h3, article/section) "
            "помогает выделять пассажи для retrieval — машиночитаемость контента."
        ),
    ),
    FactorWeight(
        factor="entity_graph",
        weight=8.0,
        layer=COMPREHENSION,
        availability="future",
        description=(
            "Связность сущностей через @id (knowledge-graph) усиливает понимание отношений "
            "между объектами сайта. P2 извлекает только типы, не @id-граф — приходит как "
            "deferred до экстрактора P6+ (не штрафует)."
        ),
    ),
    FactorWeight(
        factor="recency",
        weight=5.0,
        layer=COMPREHENSION,
        availability="future",
        description=(
            "Сигналы свежести (dateModified/datePublished) — LLM предпочитают актуальные "
            "источники. P2 пока не извлекает даты — приходит как deferred до P6+ (не штрафует)."
        ),
    ),
)

WEIGHTS: Final[tuple[FactorWeight, ...]] = (*_DISCOVERY, *_COMPREHENSION)
"""Полная весовая модель Score. Порядок = порядок раскрытия компонентов пользователю."""

WEIGHTS_BY_FACTOR: Final[MappingProxyType[str, FactorWeight]] = MappingProxyType(
    {fw.factor: fw for fw in WEIGHTS},
)
"""Индекс `factor` → `FactorWeight` для джойна движка с `audit_summary`."""

# --------------------------------------------------------------------------- #
# Инвариант §6.5 — llms.txt структурно вне Score                               #
# --------------------------------------------------------------------------- #
#
# `llms.txt` — Integration-layer артефакт (генерируется в патчах, фаза C), НЕ доказанный
# citation-рычаг. Он ОТСУТСТВУЕТ в `WEIGHTS` намеренно. Не добавляй сюда `llms_txt` без
# ADR и подписи founder — это нарушит инвариант charter §6.5 / FR-1.3 AC-2.
EXCLUDED_FROM_SCORE: Final[tuple[str, ...]] = ("llms_txt",)
"""Замороженный сторож: факторы, которым запрещено весить в Score (§6.5). Ключ для grep/AC-2."""


def _verify_weight_model() -> None:
    """Fail-fast инвариант-чек при импорте: сумма весов и исключение llms.txt.

    Ловит дрейф модели ещё на импорте, а не в рантайме расчёта. Использует `raise` (не
    `assert`) — переживает `python -O` и не триггерит ruff S101.
    """
    total = sum(fw.weight for fw in WEIGHTS)
    if abs(total - TOTAL_WEIGHT) > _WEIGHT_SUM_TOLERANCE:
        msg = f"сумма весов {total} ≠ {TOTAL_WEIGHT} — весовая модель Score сломана"
        raise RuntimeError(msg)
    for excluded in EXCLUDED_FROM_SCORE:
        if excluded in WEIGHTS_BY_FACTOR:
            msg = (
                f"фактор {excluded!r} запрещён в Score (charter §6.5 / FR-1.3), но найден в WEIGHTS"
            )
            raise RuntimeError(msg)


_verify_weight_model()
