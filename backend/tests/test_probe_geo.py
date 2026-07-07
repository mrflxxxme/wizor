"""Unit: §6.4/NFR-2 dual-geo probe (AC-2) — иностранная модель НИКОГДА не с РФ-egress.

Проверяет структурный предохранитель `probe.geo` без единого реального вызова:
egress выводится из семейства модели; `assert_probe_geo` рвёт «РФ-IP к ChatGPT» и
иностранную модель без зарубежного прокси; отображение модель→провайдер согласовано с P4.
"""

from __future__ import annotations

import pytest

from wizor.llm_router.schemas import FOREIGN_PROVIDERS, RU_PROVIDERS
from wizor.probe.geo import (
    MODEL_EGRESS,
    ProbeGeoViolationError,
    assert_probe_geo,
    egress_for_model,
    provider_for_model,
)
from wizor.probe.schemas import FOREIGN_MODELS, RU_MODELS, ModelId

_ALL_MODELS: tuple[ModelId, ...] = (*RU_MODELS, *FOREIGN_MODELS)


# --- Отображение модель → egress выводится из семейства (§6.4) --------------------------


def test_egress_foreign_for_foreign_models() -> None:
    for model in FOREIGN_MODELS:
        assert egress_for_model(model) == "foreign"


def test_egress_ru_for_ru_models() -> None:
    for model in RU_MODELS:
        assert egress_for_model(model) == "ru"


def test_model_egress_map_covers_all_and_no_foreign_is_ru() -> None:
    """AC-2 sweep: карта покрывает все модели и НИ ОДНА иностранная не помечена ``ru``."""
    assert set(MODEL_EGRESS) == set(_ALL_MODELS)
    assert all(MODEL_EGRESS[m] == "foreign" for m in FOREIGN_MODELS)
    assert all(MODEL_EGRESS[m] == "ru" for m in RU_MODELS)


# --- Отображение модель → P4-провайдер согласовано с llm_router ------------------------


def test_provider_mapping_is_exact() -> None:
    assert provider_for_model("alice_yandex") == "yandexgpt"
    assert provider_for_model("gigachat") == "gigachat"
    assert provider_for_model("chatgpt") == "openai"
    assert provider_for_model("perplexity") == "perplexity"


def test_foreign_models_map_to_foreign_providers() -> None:
    assert all(provider_for_model(m) in FOREIGN_PROVIDERS for m in FOREIGN_MODELS)


def test_ru_models_map_to_ru_providers() -> None:
    assert all(provider_for_model(m) in RU_PROVIDERS for m in RU_MODELS)


# --- assert_probe_geo: «РФ-IP к ChatGPT» отвергается структурно (сердце AC-2) -----------


def test_assert_rejects_ru_egress_for_every_foreign_model() -> None:
    """Пытаемся сломать инвариант: любая иностранная модель с ``ru`` egress обязана упасть."""
    for model in FOREIGN_MODELS:
        with pytest.raises(ProbeGeoViolationError, match=r"§6\.4"):
            assert_probe_geo(model, "ru", foreign_proxy_configured=True)


def test_assert_rejects_foreign_model_without_proxy() -> None:
    for model in FOREIGN_MODELS:
        with pytest.raises(ProbeGeoViolationError, match=r"прокси"):
            assert_probe_geo(model, "foreign", foreign_proxy_configured=False)


def test_assert_accepts_foreign_model_with_foreign_egress_and_proxy() -> None:
    for model in FOREIGN_MODELS:
        assert_probe_geo(model, "foreign", foreign_proxy_configured=True)  # не бросает


def test_assert_accepts_ru_model_with_ru_egress_without_proxy() -> None:
    """RU-модель легитимно идёт с РФ-egress (§6.4 бьёт только ChatGPT/Perplexity)."""
    for model in RU_MODELS:
        assert_probe_geo(model, "ru", foreign_proxy_configured=False)  # не бросает


def test_assert_rejects_ru_model_forced_to_foreign_egress() -> None:
    """Обратная несостыковка: RU-модель с ``foreign`` egress — тоже нарушение консистентности."""
    for model in RU_MODELS:
        with pytest.raises(ProbeGeoViolationError):
            assert_probe_geo(model, "foreign", foreign_proxy_configured=True)
