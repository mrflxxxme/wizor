# planner — memory

**namespace:** `agent-memory:planner`
**owned files:** `.planning/PLAN.md` (active)

## MUST-persist
- Ссылка на phase-spec активной фазы
- Список открытых вопросов по AC (до ответа founder/architect)
- Паттерны декомпозиции, которые работали/не работали (→ MEMORY-INDEX)

## MUST-NOT
- Полный код или diff
- Secrets / credentials
- Контент, принадлежащий другому агенту (только pointer)

## Retrieval queries (примеры для MEMORY-INDEX)
- `tag:plan-pattern topic:decomposition` — паттерны декомпозиции фаз
- `tag:adr topic:contracts` — ADR, затрагивающие контракты
- `tag:phase-history` — что делалось в прошлых фазах

## Pruning
Устаревший PLAN.md (фаза done) → архив в `_session-context/archive/` (делает memory-curator). В namespace удерживай только patterns и pitfalls — не сами планы.
