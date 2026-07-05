"""Валидатор JSON-LD разметки: rdflib + кастомные правила (FR-1.2, AC-4).

Проверяет каждый блок `<script type="application/ld+json">`:
1. Синтаксис JSON (`json.loads`).
2. Кастомные структурные правила schema.org (`@context`, `@type`).
3. Разбор в RDF-граф через rdflib (структурная валидность JSON-LD).

Валидация офлайн — двойная защита от SSRF (JSON-LD берётся с потенциально вредоносного
краулимого сайта, §6.1 read-only + детерминизм тестов):
1. `@context` нейтрализуется РЕКУРСИВНО для строки, списка И dict: любой remote-URL
   (`http(s)://…`, включая `["http://169.254.169.254/…"]`) заменяется на инлайновый
   `@vocab`; инлайновые term-мапы сохраняются. Удалённых URL в документе не остаётся.
2. На время разбора JSON-LD document-loader rdflib переводится в офлайн-режим: любой
   сетевой резолвинг remote-`@context` блокируется (не сетевой вызов), а не выполняется.
Итог — `SchemaValidation` (AC-4: валидный → `schema_valid=true`; невалидный → `false`
+ причины в `errors`).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import rdflib.plugins.shared.jsonld.context as _jsonld_context
from rdflib import Graph

from wizor.crawler.schemas import SchemaValidation

# Схемы, резолвинг которых означал бы сетевой доступ (SSRF-поверхность).
_REMOTE_SCHEMES = ("http://", "https://")


class _RemoteContextBlockedError(RuntimeError):
    """Попытка rdflib резолвить @context по сети заблокирована офлайн-загрузчиком."""


@contextmanager
def _offline_jsonld_loader() -> Iterator[None]:
    """Перевести JSON-LD-парсер rdflib в офлайн: любой remote-`@context` → ошибка, не сеть.

    Подменяет `source_to_json`, используемый `_fetch_context` для загрузки remote-контекста:
    str-URL с http(s)-схемой блокируется до сетевого вызова. Комбинируется с полной
    нейтрализацией `@context` (defense-in-depth): в норме сюда remote-URL уже не доходит.
    """
    original = _jsonld_context.source_to_json  # type: ignore[attr-defined]

    def _blocked(source: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(source, str) and source.lower().startswith(_REMOTE_SCHEMES):
            msg = f"remote @context resolution blocked (offline): {source!r}"
            raise _RemoteContextBlockedError(msg)
        return original(source, *args, **kwargs)

    _jsonld_context.source_to_json = _blocked  # type: ignore[attr-defined]
    try:
        yield
    finally:
        _jsonld_context.source_to_json = original  # type: ignore[attr-defined]


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
    """Разобрать нейтрализованный документ в RDF-граф через rdflib (офлайн, без SSRF)."""
    offline_doc = _neutralize_context(parsed)
    try:
        with _offline_jsonld_loader():
            Graph().parse(data=json.dumps(offline_doc), format="json-ld")
    except _RemoteContextBlockedError as exc:
        errors.append(f"блок #{index}: remote @context заблокирован (офлайн-инвариант) — {exc}")
    except Exception as exc:
        errors.append(f"блок #{index}: rdflib не смог разобрать JSON-LD — {exc}")


def _neutralize_context(node: Any) -> Any:
    """Рекурсивно нейтрализовать любой `@context` документа — rdflib работает офлайн.

    Обходит весь документ; на каждом ключе `@context` вызывает нейтрализацию значения
    (строка/список/dict). Обычные поля обходятся рекурсивно (вложенные узлы тоже могут
    нести свой `@context`).
    """
    if isinstance(node, list):
        return [_neutralize_context(item) for item in node]
    if isinstance(node, dict):
        result: dict[str, Any] = {}
        for key, value in node.items():
            if key == "@context":
                result[key] = _neutralize_context_value(value)
            else:
                result[key] = _neutralize_context(value)
        return result
    return node


def _neutralize_context_value(value: Any) -> Any:
    """Нейтрализовать значение `@context`: remote-URL-строку → инлайновый `@vocab`.

    - str: remote-URL (`http(s)://`) → `{"@vocab": …}`; прочие строки сохраняются как есть.
    - list: поэлементно (`["https://schema.org", {...}]` → vocab + инлайновая мапа).
    - dict: инлайновая term-мапа — сетевой резолв не нужен; вложенный `@context` нейтрализуем.
    """
    if isinstance(value, str):
        if value.lower().startswith(_REMOTE_SCHEMES):
            vocab = value if value.endswith(("/", "#")) else value + "/"
            return {"@vocab": vocab}
        return value
    if isinstance(value, list):
        return [_neutralize_context_value(item) for item in value]
    if isinstance(value, dict):
        return {
            key: (_neutralize_context_value(val) if key == "@context" else val)
            for key, val in value.items()
        }
    return value


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
