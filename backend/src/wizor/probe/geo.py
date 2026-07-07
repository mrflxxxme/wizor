"""§6.4/NFR-2 СТРУКТУРНОЕ enforcement dual-geo probe (AC-2).

Священный инвариант платформы: **ни один probe к ChatGPT/Perplexity не уходит с РФ-IP**.
Здесь он закодирован СТРУКТУРНО (не комментарием), в трёх звеньях единого источника истины
(константы `RU_MODELS`/`FOREIGN_MODELS` из шва `probe.schemas`):

* ``egress_for_model`` — гео-класс модели выводится ИЗ семейства модели (иностранная ⇒
  ``foreign``, RU ⇒ ``ru``); одна точка отображения, дрейф невозможен.
* ``provider_for_model`` — модель → P4-провайдер (alice_yandex→yandexgpt, gigachat→gigachat,
  chatgpt→openai, perplexity→perplexity), чтобы диспатч шёл через реюз адаптеров P4.
* ``assert_probe_geo`` — предохранитель ПЕРЕД диспатчем: рвёт любое решение, где иностранная
  модель получила бы РФ-egress ИЛИ была бы отправлена без сконфигурированного зарубежного
  прокси. Вызывается раннером на КАЖДЫЙ прогон; нарушение → :class:`ProbeGeoViolationError`.

Раннер вычисляет egress исключительно через ``egress_for_model`` (не принимает его извне),
поэтому вызывающий код не может подсунуть иностранной модели РФ-egress в обход проверки.
"""

from __future__ import annotations

from wizor.llm_router.schemas import Provider
from wizor.probe.schemas import FOREIGN_MODELS, RU_MODELS, Egress, ModelId

# Модель → P4-провайдер (реюз адаптеров llm_router.providers). Иностранные модели ⇒
# иностранные провайдеры (egress выводится отдельно из семейства модели, не отсюда).
_MODEL_PROVIDER: dict[ModelId, Provider] = {
    "alice_yandex": "yandexgpt",
    "gigachat": "gigachat",
    "chatgpt": "openai",
    "perplexity": "perplexity",
}


class ProbeGeoViolationError(RuntimeError):
    """§6.4/NFR-2 нарушено: иностранная probe-модель получила бы РФ-egress или ушла без прокси."""


def egress_for_model(model: ModelId) -> Egress:
    """Гео-класс egress модели из её семейства: иностранная ⇒ ``foreign``, RU ⇒ ``ru`` (§6.4).

    Единственная точка отображения модель→egress: раннер обязан брать egress отсюда, а не
    принимать снаружи — иначе «РФ-IP к ChatGPT» стало бы конструктивно возможным.
    """
    return "foreign" if model in FOREIGN_MODELS else "ru"


# Полное отображение модель→egress, выведенное из шва (для аудита/логов; тот же источник).
MODEL_EGRESS: dict[ModelId, Egress] = {
    model: egress_for_model(model) for model in (*RU_MODELS, *FOREIGN_MODELS)
}


def provider_for_model(model: ModelId) -> Provider:
    """P4-провайдер для probe-модели (реюз адаптеров llm_router)."""
    return _MODEL_PROVIDER[model]


def assert_probe_geo(
    model: ModelId,
    egress: Egress,
    *,
    foreign_proxy_configured: bool,
) -> None:
    """Структурный предохранитель §6.4/NFR-2 — вызывается ПЕРЕД каждым диспатчем probe.

    Рвёт (`ProbeGeoViolationError`), если:

    1. фактический ``egress`` не совпадает с обязательным для семейства модели
       (иностранная модель с ``ru`` egress = «РФ-IP к ChatGPT», запрещено);
    2. иностранная модель отправляется без сконфигурированного зарубежного прокси
       (``foreign_proxy_configured=False``) — тогда probe невозможен, но и РФ-fallback
       недопустим: диспатч обязан быть отклонён, а не тихо переведён на РФ-IP.

    ``foreign_proxy_configured`` вызывающий передаёт по ФАКТУ прокси, взятого для этого
    прогона (``proxy is not None``), а не по глобальному конфигу — привязка максимально тесная.
    """
    required = egress_for_model(model)
    if egress != required:
        msg = (
            f"probe-geo нарушен: модель {model!r} требует egress={required!r}, "
            f"получено {egress!r} (§6.4/NFR-2: иностранная модель — только зарубежная нода, "
            f"ноль РФ-IP к ChatGPT/Perplexity)."
        )
        raise ProbeGeoViolationError(msg)
    if model in FOREIGN_MODELS and not foreign_proxy_configured:
        msg = (
            f"probe-geo нарушен: иностранная модель {model!r} без зарубежного прокси "
            f"(§6.4/NFR-2). Диспатч отклонён — тихий РФ-fallback запрещён."
        )
        raise ProbeGeoViolationError(msg)
