"""Unit: 152-ФЗ резидентность в настройках (инвариант §6.6 / NFR-1)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wizor.core.config import Settings


def test_default_region_is_ru() -> None:
    settings = Settings()
    assert settings.data_region == "ru-central1"


def test_non_ru_region_rejected() -> None:
    # Любой не-РФ регион должен валить конструирование настроек.
    with pytest.raises(ValidationError):
        Settings(data_region="us-east1")


def test_eu_region_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(data_region="eu-west1")
