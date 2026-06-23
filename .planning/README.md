# `.planning/` — навигация

Структура планирования WIZOR. Источник истины по воркфлоу — [`_meta/BUILD-CHARTER.md`](_meta/BUILD-CHARTER.md); по продукту — [`PRD.md`](PRD.md).

## Bootstrap-порядок чтения (для агента)
1. [`_meta/BUILD-CHARTER.md`](_meta/BUILD-CHARTER.md) — charter (целиком, 1×/сессия)
2. [`STATUS.md`](STATUS.md) + [`HANDOFF.md`](HANDOFF.md) — где мы сейчас
3. phase-spec активной фазы — [`roadmap/`](roadmap/)
4. затронутые контракты — [`contracts/`](contracts/)
5. точечный recall — [`MEMORY-INDEX.md`](MEMORY-INDEX.md)

## Карта каталога

| Путь | Что | Кто ведёт |
|---|---|---|
| `PRD.md` | ТЗ продукта (v0.2) | Product/founder |
| `_meta/BUILD-CHARTER.md` | **Keystone:** воркфлоу, форматы, роадмап, инварианты | architect (через ADR) |
| `_meta/{conventions,stack,glossary,README}.md` | справочная библиотека (grep, не full-read) | architect |
| `PROJECT.md` | обзор проекта, USP, North Star | founder/architect |
| `ROADMAP.md` | роадмап P0–P10 + рамочные B/C | planner |
| `roadmap/PNN-*.md` | детальные phase-spec'ы (goal/scope/FR/AC/gate) | planner |
| `decisions/ADR-*.md` | архитектурные решения (16 + template) | architect |
| `contracts/<ctx>/` | контракты bounded-context'ов (стабы + JIT) | architect/specialists |
| `gates/` | exit-гейты фаз (JSON-schema + P0/A→B) | verifier + founder |
| `STATUS.md` | rolling-состояние | memory-curator |
| `HANDOFF.md` | снапшот сессии (≤2 KB) | memory-curator |
| `JOURNAL.md` | append-only лог (ротация >300 строк) | memory-curator |
| `PHASE-HISTORY.md` | история завершённых фаз | memory-curator |
| `MEMORY-INDEX.md` | индекс recall (tag→pointer) | memory-curator |
| `OPEN-QUESTIONS.md` | открытые вопросы продукта | founder |
| `PLACEHOLDERS.md` | реестр TBD-токенов | founder |
| `_session-context/` | пост-аудиты (AUDIT-*) + архив | auditor/memory-curator |
