"""Unit: валидатор JSON-LD — валидный vs намеренно невалидный (AC-4)."""

from __future__ import annotations

import json

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
