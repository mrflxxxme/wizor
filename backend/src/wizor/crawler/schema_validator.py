"""Валидатор JSON-LD разметки: rdflib + кастомные правила (FR-1.2, AC-4).

Проверяет каждый блок `<script type="application/ld+json">`:
1. Синтаксис JSON (`json.loads`).
2. Кастомные структурные правила schema.org (`@context`, `@type`).
3. Разбор в RDF-граф через rdflib (структурная валидность JSON-LD).

Валидация полностью офлайн (инвариант §6.1 read-only + детерминизм тестов): строковые
`@context` (обычно URL schema.org) нейтрализуются в инлайновый `@vocab`, поэтому rdflib
НЕ ходит в сеть за удалённым контекстом. Итог — `SchemaValidation` (AC-4: валидный →
`schema_valid=true`; невалидный → `false` + причины в `errors`).
"""

from __future__ import annotations

import json
from typing import Any

from rdflib import Graph

from wizor.crawler.schemas import SchemaValidation


def validate_json_ld(blocks: list[str]) -> SchemaValidation:
    """Провалидировать набор JSON-LD блоков страницы/сайта.

    Пустой набор → вакуумно валиден (нечего проверять). Любой невалидный блок делает
    итог невалидным, но валидация остальных продолжается (все причины собираются).
    """
    errors: list[str] = []
    types_found: set[str] = set()

    for index, block in enumerate(blocks):
        parsed = _parse_json(block, index, errors)
        if parsed is None:
            continue
        _check_structure(parsed, index, errors)
        types_found.update(_collect_types(parsed))
        _rdflib_parse(parsed, index, errors)

    return SchemaValidation(
        schema_valid=not errors,
        types_found=sorted(types_found),
        errors=errors,
    )


def _parse_json(block: str, index: int, errors: list[str]) -> Any | None:
    """Разобрать JSON; при синтаксической ошибке дописать причину и вернуть None."""
    try:
        return json.loads(block)
    except (json.JSONDecodeError, TypeError) as exc:
        errors.append(f"блок #{index}: невалидный JSON — {exc}")
        return None


def _check_structure(parsed: Any, index: int, errors: list[str]) -> None:
    """Кастомные правила schema.org: наличие @context и @type в каждом узле."""
    nodes = parsed if isinstance(parsed, list) else [parsed]
    for node in nodes:
        if not isinstance(node, dict):
            errors.append(
                f"блок #{index}: JSON-LD узел должен быть объектом, получено {type(node).__name__}"
            )
            continue
        graph_items = node.get("@graph")
        if isinstance(graph_items, list):
            if "@context" not in node:
                errors.append(f"блок #{index}: отсутствует @context у @graph-контейнера")
            for item in graph_items:
                _check_node_type(item, index, errors)
            continue
        if "@context" not in node:
            errors.append(f"блок #{index}: отсутствует обязательный @context (schema.org)")
        _check_node_type(node, index, errors)


def _check_node_type(node: Any, index: int, errors: list[str]) -> None:
    """Узел JSON-LD обязан объявлять @type."""
    if not isinstance(node, dict):
        errors.append(f"блок #{index}: элемент @graph должен быть объектом")
    elif "@type" not in node:
        errors.append(f"блок #{index}: отсутствует обязательный @type")


def _rdflib_parse(parsed: Any, index: int, errors: list[str]) -> None:
    """Разобрать нейтрализованный (офлайн) документ в RDF-граф через rdflib."""
    offline_doc = _neutralize_context(parsed)
    try:
        Graph().parse(data=json.dumps(offline_doc), format="json-ld")
    except Exception as exc:
        errors.append(f"блок #{index}: rdflib не смог разобрать JSON-LD — {exc}")


def _neutralize_context(node: Any) -> Any:
    """Заменить строковые @context (URL) на инлайновый @vocab — rdflib работает офлайн."""
    if isinstance(node, list):
        return [_neutralize_context(item) for item in node]
    if isinstance(node, dict):
        result: dict[str, Any] = {}
        for key, value in node.items():
            if key == "@context" and isinstance(value, str):
                vocab = value if value.endswith(("/", "#")) else value + "/"
                result[key] = {"@vocab": vocab}
            else:
                result[key] = _neutralize_context(value)
        return result
    return node


def _collect_types(node: Any) -> list[str]:
    """Рекурсивно собрать значения @type (объекты, списки, @graph)."""
    types: list[str] = []
    if isinstance(node, dict):
        raw = node.get("@type")
        if isinstance(raw, str):
            types.append(raw)
        elif isinstance(raw, list):
            types.extend(t for t in raw if isinstance(t, str))
        for value in node.values():
            types.extend(_collect_types(value))
    elif isinstance(node, list):
        for item in node:
            types.extend(_collect_types(item))
    return types
