"""Unit: валидатор JSON-LD — валидный vs намеренно невалидный (AC-4) + офлайн/SSRF (F2)."""

from __future__ import annotations

import json

import pytest

import wizor.crawler.schema_validator as sv
from wizor.crawler.schema_validator import validate_json_ld

_VALID = json.dumps(
    {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Acme",
        "url": "https://acme.ru",
    }
)
_VALID_FAQ = json.dumps(
    {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": "Вопрос?",
                "acceptedAnswer": {"@type": "Answer", "text": "Ответ"},
            }
        ],
    }
)


def test_valid_json_ld() -> None:
    result = validate_json_ld([_VALID])
    assert result.schema_valid is True
    assert "Organization" in result.types_found
    assert result.errors == []


def test_valid_nested_types() -> None:
    result = validate_json_ld([_VALID_FAQ])
    assert result.schema_valid is True
    assert {"FAQPage", "Question", "Answer"} <= set(result.types_found)


def test_invalid_json_syntax() -> None:
    result = validate_json_ld(['{"@context": "https://schema.org", "@type": '])
    assert result.schema_valid is False
    assert any("невалидный JSON" in e for e in result.errors)


def test_invalid_missing_type() -> None:
    result = validate_json_ld([json.dumps({"@context": "https://schema.org", "name": "x"})])
    assert result.schema_valid is False
    assert any("@type" in e for e in result.errors)


def test_invalid_missing_context() -> None:
    result = validate_json_ld([json.dumps({"@type": "Organization", "name": "x"})])
    assert result.schema_valid is False
    assert any("@context" in e for e in result.errors)


def test_mixed_valid_and_invalid() -> None:
    result = validate_json_ld([_VALID, "{broken"])
    assert result.schema_valid is False
    # Валидный блок всё равно учтён (тип собран), но итог невалиден из-за битого.
    assert "Organization" in result.types_found
    assert len(result.errors) == 1


def test_empty_is_vacuously_valid() -> None:
    result = validate_json_ld([])
    assert result.schema_valid is True
    assert result.types_found == []


# --- F2: list/dict @context — офлайн-нейтрализация + отсутствие сетевого резолва (SSRF) ---

_LIST_CONTEXT = json.dumps(
    {
        "@context": ["https://schema.org", {"ext": "https://example.ru/vocab#"}],
        "@type": "Organization",
        "name": "Acme",
    }
)

# Вредоносный краулимый JSON-LD: remote @context на metadata-эндпоинт (SSRF-попытка).
_MALICIOUS_CONTEXT = json.dumps(
    {
        "@context": ["http://169.254.169.254/latest/meta-data/", {"x": "urn:x:"}],
        "@type": "Organization",
        "name": "evil",
    }
)


def test_list_context_still_validates() -> None:
    """Список @context (URL + инлайновая мапа) валиден и офлайн-нейтрализован."""
    result = validate_json_ld([_LIST_CONTEXT])
    assert result.schema_valid is True
    assert "Organization" in result.types_found


def test_malicious_context_no_network_and_no_false_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """@context:[metadata-URL] НЕ провоцирует сетевой резолв и НЕ роняет валидацию в false.

    Патчим `source_to_json` так, что любой str-URL = провал теста: если rdflib попытается
    сходить в сеть за remote-контекстом, тест упадёт. Полная нейтрализация @context не
    оставляет remote-URL, поэтому вызова быть не должно, а разметка остаётся валидной.
    """
    original = sv._jsonld_context.source_to_json

    def _guarded(source: object, *args: object, **kwargs: object) -> object:
        if isinstance(source, str) and source.lower().startswith(("http://", "https://")):
            pytest.fail(f"сетевой резолв remote @context: {source!r} (SSRF!)")
        return original(source, *args, **kwargs)  # type: ignore[operator]

    monkeypatch.setattr(sv._jsonld_context, "source_to_json", _guarded)

    result = validate_json_ld([_MALICIOUS_CONTEXT])

    assert result.schema_valid is True
    assert "Organization" in result.types_found
    assert result.errors == []


def test_neutralize_removes_remote_urls_from_list_context() -> None:
    """После нейтрализации в list-@context не остаётся remote-URL-строк (только @vocab/мапы)."""
    neutralized = sv._neutralize_context(json.loads(_MALICIOUS_CONTEXT))
    ctx = neutralized["@context"]
    assert isinstance(ctx, list)
    assert not any(isinstance(item, str) and item.startswith("http") for item in ctx)
    assert {"@vocab": "http://169.254.169.254/latest/meta-data/"} in ctx


def test_offline_loader_blocks_remote_context() -> None:
    """Офлайн-загрузчик рвёт remote str-URL исключением, а не сетевым вызовом (defense-in-depth)."""
    with sv._offline_jsonld_loader(), pytest.raises(sv._RemoteContextBlockedError):
        sv._jsonld_context.source_to_json("http://169.254.169.254/latest/meta-data/")
